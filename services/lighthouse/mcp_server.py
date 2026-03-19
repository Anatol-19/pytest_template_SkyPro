"""
MCP-сервер для Lighthouse Automation.

Экспонирует tools для запуска Lighthouse CLI, сбора CrUX,
просмотра контуров/роутов и проверки статуса.

Запуск: python services/lighthouse/mcp_server.py
Регистрация: claude mcp add lighthouse -- python C:/Study/pytest_template_SkyPro/services/lighthouse/mcp_server.py
"""

import configparser
import os
import shutil
import sys
import threading
import time
import traceback
import uuid
from typing import List, Optional, Dict, Any, Callable

# MCP stdio: stdout зарезервирован для JSON-RPC.
# Сохраняем оригинальный stdout для FastMCP, а print() → stderr.
_real_stdout = sys.stdout
sys.stdout = sys.stderr

# Корень проекта — три уровня вверх от этого файла
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
# MCP stdio-процесс может стартовать из любой cwd — фиксируем на корень проекта
os.chdir(ROOT_DIR)

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Загружаем .env (абсолютный путь — не зависит от cwd)
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "config_lighthouse.env")
load_dotenv(dotenv_path, override=True)

import services.lighthouse.configs.config_lighthouse as cfg
from contextlib import contextmanager

CONFIG_PATH = cfg.CONFIG_PATH


@contextmanager
def _suppress_stdout():
    """Перенаправляет stdout в stderr на время выполнения блока.
    Защищает MCP JSON-RPC поток от print() внутри сервисного кода."""
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old
ROUTES_CONFIG_PATH = cfg.ROUTES_CONFIG_PATH

mcp = FastMCP("lighthouse")


def _read_environments() -> dict:
    """Читает все контуры из base_urls.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    current = config["environments"]["current"]
    envs = {}
    for section in config.sections():
        if section == "environments":
            continue
        base_url = config[section].get("BASE_URL", "—")
        envs[section] = {
            "BASE_URL": base_url,
            "active": section == current,
        }
    return envs


def _read_routes() -> dict:
    """Читает роуты из routes.ini."""
    config = configparser.ConfigParser()
    config.read(ROUTES_CONFIG_PATH, encoding="utf-8")
    if "routes" not in config:
        return {}
    return dict(config["routes"])


# ─── Мини-очередь заданий (fire-and-forget + статус) ─────────────────────────

JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()


def _register_job(kind: str, payload: dict, runner: Callable[[], str]) -> str:
    job_id = uuid.uuid4().hex[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {
            "kind": kind,
            "payload": payload,
            "status": "queued",
            "started_at": None,
            "ended_at": None,
            "result": None,
            "error": None,
        }

    def _worker():
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "running"
            JOBS[job_id]["started_at"] = time.time()
        try:
            res = runner()
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "done"
                JOBS[job_id]["ended_at"] = time.time()
                JOBS[job_id]["result"] = res
        except Exception as e:  # noqa: BLE001
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["ended_at"] = time.time()
                JOBS[job_id]["error"] = f"{e} | {traceback.format_exc(limit=2)}"

    threading.Thread(target=_worker, daemon=True).start()
    return job_id


# ─── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def run_lighthouse(
    routes: List[str],
    device: str,
    iterations: int = 10,
    environment: Optional[str] = None,
) -> str:
    """Запускает Lighthouse CLI для указанных роутов.

    Переключает контур (если указан), прогоняет N итераций,
    агрегирует результаты и записывает в Google Sheets.

    Args:
        routes: Список ключей роутов из routes.ini (например ["home", "login"]).
        device: Тип устройства — "desktop" или "mobile".
        iterations: Количество итераций (по умолчанию 10).
        environment: Контур (например "VRP_DEV"). Если не указан — используется текущий.
    """
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService

        env_name = environment or cfg.get_current_environment()
        base_url = cfg.get_base_url(environment=env_name)

        service = SpeedtestService(environment=env_name)
        service.run_local_tests(
            route_keys=routes,
            device_type=device,
            n_iteration=iterations,
            base_url=base_url,
        )

    return (
        f"Lighthouse CLI завершён.\n"
        f"Контур: {env_name} ({base_url})\n"
        f"Роуты: {', '.join(routes)}\n"
        f"Устройство: {device}\n"
        f"Итераций: {iterations}\n"
        f"Результаты записаны в Google Sheets."
    )


@mcp.tool()
def run_crux(
    routes: List[str],
    device: str,
    environment: Optional[str] = None,
) -> str:
    """Собирает CrUX данные (Chrome User Experience Report) для указанных роутов.

    CrUX доступен только для PROD-контуров (*_PROD).

    Args:
        routes: Список ключей роутов из routes.ini.
        device: Тип устройства — "desktop" или "mobile".
        environment: Контур (рекомендуется *_PROD). Если не указан — текущий.
    """
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService

        env_name = environment or cfg.get_current_environment()
        base_url = cfg.get_base_url(environment=env_name)

        if "PROD" not in env_name.upper():
            return (
                f"Внимание: CrUX данные обычно доступны только для PROD-контуров. "
                f"Текущий контур: {env_name}. Попробуйте VRS_PROD или VRP_PROD."
            )

        service = SpeedtestService(environment=env_name)
        service.run_crux_data_collection(
            route_keys=routes,
            device_type=device,
            base_url=base_url,
        )

    return (
        f"CrUX сбор завершён.\n"
        f"Контур: {env_name} ({base_url})\n"
        f"Роуты: {', '.join(routes)}\n"
        f"Устройство: {device}\n"
        f"Результаты записаны в Google Sheets."
    )


@mcp.tool()
def list_environments() -> str:
    """Возвращает список всех доступных контуров (environments) из base_urls.ini.

    Показывает название контура, BASE_URL и какой контур сейчас активен.
    """
    envs = _read_environments()
    lines = ["Доступные контуры:\n"]
    for name, info in envs.items():
        marker = " ← текущий" if info["active"] else ""
        lines.append(f"  {name}: {info['BASE_URL']}{marker}")
    return "\n".join(lines)


@mcp.tool()
def list_routes() -> str:
    """Возвращает список роутов из routes.ini.

    Показывает ключ роута и соответствующий путь.
    """
    routes = _read_routes()
    if not routes:
        return "Роуты не найдены в routes.ini."
    lines = ["Доступные роуты:\n"]
    for key, path in routes.items():
        lines.append(f"  {key}: {path}")
    return "\n".join(lines)


@mcp.tool()
def get_status() -> str:
    """Проверяет готовность системы: наличие Lighthouse CLI и подключение к Google Sheets.

    Возвращает статус каждого компонента.
    """
    with _suppress_stdout():
        results = []

        lighthouse_ok = shutil.which("lighthouse") is not None
        results.append(
            f"Lighthouse CLI: {'✓ установлен' if lighthouse_ok else '✗ не найден (npm i -g lighthouse)'}"
        )

        try:
            creds_path = cfg.get_google_creds_path()
            results.append(f"Google Sheets credentials: ✓ {creds_path}")
        except (ValueError, FileNotFoundError) as e:
            results.append(f"Google Sheets credentials: ✗ {e}")

        sheet_id = os.getenv("GS_SHEET_ID")
        results.append(
            f"GS_SHEET_ID: {'✓ задан' if sheet_id else '✗ не задан'}"
        )

        try:
            env = cfg.get_current_environment()
            url = cfg.get_base_url()
            results.append(f"Текущий контур: {env} ({url})")
        except Exception as e:
            results.append(f"Текущий контур: ✗ ошибка — {e}")

    return "\n".join(results)


# ─── Асинхронные задания (API для внешнего агента) ──────────────────────────


def _format_job(job_id: str, data: dict) -> str:
    payload = data.get("payload", {})
    env = payload.get("environment") or payload.get("env") or "—"
    routes = payload.get("routes") or payload.get("route_keys") or []
    device = payload.get("device", "—")
    return (
        f"{job_id}: {data['status']} | {data.get('kind')} | env={env} | "
        f"routes={routes} | device={device}"
    )


@mcp.tool()
def enqueue_lighthouse(routes: List[str], device: str, iterations: int = 5, environment: Optional[str] = None) -> str:
    """Добавляет задание на Lighthouse CLI в очередь и сразу возвращает job_id."""

    def _runner() -> str:
        with _suppress_stdout():
            from services.lighthouse.pagespeed_service import SpeedtestService

            env_name = environment or cfg.get_current_environment()
            base_url = cfg.get_base_url(environment=env_name)
            service = SpeedtestService(environment=env_name)
            service.run_local_tests(route_keys=routes, device_type=device, n_iteration=iterations, base_url=base_url)
            return f"done: env={env_name}, device={device}, routes={routes}, iterations={iterations}"

    job_id = _register_job(
        kind="lighthouse_cli",
        payload={"routes": routes, "device": device, "iterations": iterations, "environment": environment},
        runner=_runner,
    )
    return f"job_id={job_id} (lighthouse_cli queued)"


@mcp.tool()
def enqueue_crux(routes: List[str], device: str, environment: Optional[str] = None) -> str:
    """Добавляет задание на CrUX сбор в очередь и возвращает job_id."""

    def _runner() -> str:
        with _suppress_stdout():
            from services.lighthouse.pagespeed_service import SpeedtestService

            env_name = environment or cfg.get_current_environment()
            base_url = cfg.get_base_url(environment=env_name)
            service = SpeedtestService(environment=env_name)
            service.run_crux_data_collection(route_keys=routes, device_type=device, base_url=base_url)
            return f"done: env={env_name}, device={device}, routes={routes}"

    job_id = _register_job(
        kind="crux",
        payload={"routes": routes, "device": device, "environment": environment},
        runner=_runner,
    )
    return f"job_id={job_id} (crux queued)"


@mcp.tool()
def list_jobs() -> str:
    """Возвращает краткий статус по всем заданиям в очереди."""
    with JOBS_LOCK:
        if not JOBS:
            return "Очередь пуста."
        lines = [_format_job(jid, data) for jid, data in JOBS.items()]
    return "\n".join(lines)


@mcp.tool()
def job_status(job_id: str) -> str:
    """Возвращает статус конкретного задания."""
    with JOBS_LOCK:
        data = JOBS.get(job_id)
        if not data:
            return f"Задание {job_id} не найдено."
        return _format_job(job_id, data)


if __name__ == "__main__":
    # Возвращаем stdout для FastMCP (JSON-RPC транспорт)
    sys.stdout = _real_stdout
    mcp.run()
