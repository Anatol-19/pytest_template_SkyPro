"""
MCP-сервер для Zoho Projects.

Экспонирует tools для работы с задачами, багами, пользователями,
milestone'ами и таск-листами проекта.

Запуск: python services/ZOHO/mcp_server.py
Регистрация (user scope):
    claude mcp add zoho --scope user -- python /полный/путь/до/services/ZOHO/mcp_server.py
"""

import os
import sys
import traceback
import time
from typing import Optional

# MCP stdio: stdout зарезервирован для JSON-RPC.
_real_stdout = sys.stdout
sys.stdout = sys.stderr

# Корень проекта — два уровня вверх от этого файла
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP

LOG_PATH = os.path.join(ROOT_DIR, "Reports", "zoho_mcp.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def _log(level: str, msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} [{level}] {msg}\n")


@contextmanager
def _suppress_stdout():
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old


mcp = FastMCP("zoho")

_api = None


def _get_api():
    global _api
    if _api is None:
        with _suppress_stdout():
            from services.ZOHO.Zoho_api_client import ZohoAPI
            _api = ZohoAPI()
    return _api


# ─── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_status() -> str:
    """Проверяет подключение к Zoho Projects API.

    Пробует получить список порталов. Показывает статус токенов и проект.
    """
    try:
        with _suppress_stdout():
            api = _get_api()
            portals = api.get_portals()
        if portals:
            return (
                f"✅ Подключение успешно.\n"
                f"Портал: {api.portal_name}\n"
                f"Проект ID: {api.project_id}\n"
                f"Регион: {os.getenv('ZOHO_REGION', 'com')}"
            )
        return "⚠️ Подключение установлено, но портал не вернул данных."
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка подключения: {e}"


@mcp.tool()
def get_tasks(
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    closed_after: Optional[str] = None,
    closed_before: Optional[str] = None,
    owner_name: Optional[str] = None,
    milestone_name: Optional[str] = None,
    tasklist_name: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Возвращает задачи проекта с фильтрацией.

    Args:
        created_after: Начало диапазона создания (YYYY-MM-DD).
        created_before: Конец диапазона создания (YYYY-MM-DD).
        closed_after: Начало диапазона закрытия (YYYY-MM-DD).
        closed_before: Конец диапазона закрытия (YYYY-MM-DD).
        owner_name: Имя ответственного (часть имени, регистронезависимо).
        milestone_name: Название milestone'а для фильтрации.
        tasklist_name: Название таск-листа для фильтрации.
        limit: Максимальное количество задач в ответе (по умолчанию 50).
    """
    try:
        with _suppress_stdout():
            api = _get_api()

            milestone_id = None
            if milestone_name:
                milestone_id = api.get_milestone_id_by_name(milestone_name)
                if not milestone_id:
                    return f"⚠️ Milestone '{milestone_name}' не найден."

            tasklist_id = None
            if tasklist_name:
                tasklist_id = api.get_tasklist_id_by_name(tasklist_name)
                if not tasklist_id:
                    return f"⚠️ Таск-лист '{tasklist_name}' не найден."

            owner_id = None
            if owner_name:
                users = api.get_users()
                matched = [u for u in users if owner_name.lower() in u.get("name", "").lower()]
                if not matched:
                    return f"⚠️ Пользователь '{owner_name}' не найден."
                owner_id = str(matched[0]["id"])

            tasks = api.get_entities_by_filter(
                entity_type="tasks",
                created_after=created_after,
                created_before=created_before,
                closed_after=closed_after,
                closed_before=closed_before,
                owner_id=owner_id,
                milestone_id=milestone_id,
                tasklist_id=tasklist_id,
            )

        if not tasks:
            return "Задачи по заданным фильтрам не найдены."

        tasks = tasks[:limit]
        lines = [f"Найдено задач: {len(tasks)}\n"]
        for t in tasks:
            status = t.get("status", {}).get("name", "—")
            owner = t.get("details", {}).get("owners", [{}])
            owner_str = ", ".join(o.get("name", "—") for o in owner) if owner else "—"
            lines.append(
                f"• [{t.get('id')}] {t.get('name', '—')}\n"
                f"  Статус: {status} | Ответственный: {owner_str}\n"
                f"  Создана: {t.get('created_time', '—')} | Дедлайн: {t.get('end_date', '—')}"
            )
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_bugs(
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    closed_after: Optional[str] = None,
    closed_before: Optional[str] = None,
    owner_name: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Возвращает баги (дефекты) проекта с фильтрацией.

    Args:
        created_after: Начало диапазона создания (YYYY-MM-DD).
        created_before: Конец диапазона создания (YYYY-MM-DD).
        closed_after: Начало диапазона закрытия (YYYY-MM-DD).
        closed_before: Конец диапазона закрытия (YYYY-MM-DD).
        owner_name: Имя ответственного (часть имени, регистронезависимо).
        limit: Максимальное количество багов в ответе (по умолчанию 50).
    """
    try:
        with _suppress_stdout():
            api = _get_api()

            owner_id = None
            if owner_name:
                users = api.get_users()
                matched = [u for u in users if owner_name.lower() in u.get("name", "").lower()]
                if not matched:
                    return f"⚠️ Пользователь '{owner_name}' не найден."
                owner_id = str(matched[0]["id"])

            bugs = api.get_entities_by_filter(
                entity_type="bugs",
                created_after=created_after,
                created_before=created_before,
                closed_after=closed_after,
                closed_before=closed_before,
                owner_id=owner_id,
            )

        if not bugs:
            return "Баги по заданным фильтрам не найдены."

        bugs = bugs[:limit]
        lines = [f"Найдено багов: {len(bugs)}\n"]
        for b in bugs:
            status = b.get("status", {}).get("type", "—")
            assignee = b.get("assignee", {}).get("name", "—") if b.get("assignee") else "—"
            lines.append(
                f"• [{b.get('id')}] {b.get('title', '—')}\n"
                f"  Статус: {status} | Ответственный: {assignee}\n"
                f"  Создан: {b.get('created_time', '—')} | Приоритет: {b.get('severity', '—')}"
            )
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_milestones() -> str:
    """Возвращает список milestone'ов проекта."""
    try:
        with _suppress_stdout():
            api = _get_api()
            milestones = api.get_entities_by_filter("milestones")

        if not milestones:
            return "Milestone'ы не найдены."

        lines = [f"Milestone'ы ({len(milestones)}):\n"]
        for m in milestones:
            status = "закрыт" if m.get("status") == "closed" else "открыт"
            lines.append(
                f"• [{m.get('id')}] {m.get('name', '—')} — {status}\n"
                f"  Дедлайн: {m.get('end_date', '—')} | Флаг: {m.get('flag', '—')}"
            )
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_tasklists() -> str:
    """Возвращает список таск-листов проекта."""
    try:
        with _suppress_stdout():
            api = _get_api()
            tasklists = api.get_entities_by_filter("tasklists")

        if not tasklists:
            return "Таск-листы не найдены."

        lines = [f"Таск-листы ({len(tasklists)}):\n"]
        for tl in tasklists:
            lines.append(f"• [{tl.get('id')}] {tl.get('name', '—')}")
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_users(search: Optional[str] = None) -> str:
    """Возвращает список пользователей проекта.

    Args:
        search: Поисковая строка — часть имени или email (регистронезависимо).
    """
    try:
        with _suppress_stdout():
            api = _get_api()
            users = api.get_users(search_term=search)

        if not users:
            return "Пользователи не найдены."

        lines = [f"Пользователи ({len(users)}):\n"]
        for u in users:
            lines.append(
                f"• [{u.get('id')}] {u.get('name', '—')} <{u.get('email', '—')}> — {u.get('role', '—')}"
            )
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_tags() -> str:
    """Возвращает теги проекта."""
    try:
        with _suppress_stdout():
            api = _get_api()
            tags = api.get_project_tags()

        if not tags:
            return "Теги не найдены."

        lines = [f"Теги ({len(tags)}):\n"]
        for t in tags:
            lines.append(f"• [{t.get('id')}] {t.get('name', '—')}")
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def create_bug(
    title: str,
    description: str,
    assignee_name: Optional[str] = None,
    priority: Optional[str] = None,
) -> str:
    """Создаёт баг в проекте.

    Args:
        title: Название бага.
        description: Описание бага.
        assignee_name: Имя ответственного (часть имени, регистронезависимо).
        priority: Приоритет — high / medium / low.
    """
    try:
        with _suppress_stdout():
            api = _get_api()

            assignee_id = None
            if assignee_name:
                users = api.get_users()
                matched = [u for u in users if assignee_name.lower() in u.get("name", "").lower()]
                if not matched:
                    return f"⚠️ Пользователь '{assignee_name}' не найден. Баг не создан."
                assignee_id = str(matched[0]["id"])

            result = api.create_bug(
                title=title,
                description=description,
                assignee_id=assignee_id,
                priority=priority,
            )

        if result:
            bug = result.get("bugs", [{}])[0] if result.get("bugs") else result
            return (
                f"✅ Баг создан.\n"
                f"ID: {bug.get('id', '—')}\n"
                f"Название: {bug.get('title', title)}\n"
                f"Статус: {bug.get('status', {}).get('type', '—')}"
            )
        return "⚠️ Баг не создан — API не вернул данные."
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_tasks_by_title(title: str) -> str:
    """Ищет задачи по названию таск-листа или milestone'а.

    Args:
        title: Название таск-листа или milestone'а для поиска.
    """
    try:
        with _suppress_stdout():
            api = _get_api()
            tasks = api.get_tasks_by_title(title)

        if not tasks:
            return f"Задачи по запросу '{title}' не найдены."

        lines = [f"Найдено задач по '{title}': {len(tasks)}\n"]
        for t in tasks:
            status = t.get("status", {}).get("name", "—")
            lines.append(f"• [{t.get('id')}] {t.get('name', '—')} — {status}")
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


@mcp.tool()
def get_bug_statuses() -> str:
    """Возвращает возможные статусы багов в проекте."""
    try:
        with _suppress_stdout():
            api = _get_api()
            statuses = api.get_bug_statuses()

        if not statuses:
            return "Статусы багов не найдены."

        lines = [f"Статусы багов ({len(statuses)}):\n"]
        for s in statuses:
            lines.append(f"• [{s.get('id')}] {s.get('name', '—')}")
        return "\n".join(lines)
    except Exception as e:
        _log("ERROR", traceback.format_exc())
        return f"❌ Ошибка: {e}"


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    _log("INFO", f"zoho mcp_server start | python={sys.version} | root={ROOT_DIR}")

    parser = argparse.ArgumentParser(description="Zoho MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Транспорт MCP (по умолчанию stdio)",
    )
    args, _ = parser.parse_known_args()

    sys.stdout = _real_stdout
    _log("INFO", f"starting FastMCP transport={args.transport}")
    try:
        mcp.run(transport=args.transport)
    except Exception:
        _log("ERROR", traceback.format_exc())
        sys.exit(1)
