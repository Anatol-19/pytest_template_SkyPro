"""
MCP-сервер для Lighthouse Automation.

Экспонирует tools для запуска Lighthouse CLI, сбора CrUX,
просмотра контуров/роутов и проверки статуса.

Запуск: python services/lighthouse/mcp_server.py
Регистрация: claude mcp add lighthouse -- python C:/Study/pytest_template_SkyPro/services/lighthouse/mcp_server.py
"""

import configparser
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from typing import List, Optional, Dict, Any

# MCP stdio: stdout зарезервирован для JSON-RPC.
# Сохраняем оригинальный stdout для FastMCP, а print() → stderr.
_real_stdout = sys.stdout
sys.stdout = sys.stderr

# Корень проекта — три уровня вверх от этого файла
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
# MCP stdio-процесс может стартовать из любой cwd — фиксируем на корень проекта
os.chdir(ROOT_DIR)

import argparse
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

DEFAULT_ITERATIONS = 5
DEFAULT_DEVICES = ["desktop", "mobile"]
JOBS_STATE_PATH = os.path.join(ROOT_DIR, "Reports", "reports_lighthouse", "mcp_jobs.json")
MCP_LOG_PATH = os.path.join(ROOT_DIR, "Reports", "reports_lighthouse", "mcp_server.log")
MAX_JOBS_HISTORY = 100
JOB_TTL_SECONDS = 7 * 24 * 60 * 60

os.makedirs(os.path.dirname(MCP_LOG_PATH), exist_ok=True)

def _write_log(level: str, message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(MCP_LOG_PATH, "a", encoding="utf-8") as file:
        file.write(f"{timestamp} [{level}] {message}\n")


def _log_info(message: str) -> None:
    _write_log("INFO", message)


def _log_exception(message: str) -> None:
    _write_log("ERROR", f"{message}\n{traceback.format_exc()}")


_log_info("mcp_server import started")
_log_info(f"python={sys.version}")
_log_info(f"root_dir={ROOT_DIR}")
_log_info(f"dotenv_path={dotenv_path}")


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


def _resolve_routes(requested: Optional[List[str]]) -> List[str]:
    available = list(_read_routes().keys())
    if not available:
        raise ValueError("Routes configuration is empty.")
    if not requested:
        return available
    normalized = [r for r in requested if r in available]
    missing = [r for r in requested if r not in normalized]
    if missing:
        raise ValueError(f"Unknown routes: {', '.join(missing)}")
    return normalized


def _resolve_devices(requested: Optional[List[str]]) -> List[str]:
    if not requested:
        return DEFAULT_DEVICES
    normalized = []
    for dev in requested:
        dev_l = dev.lower()
        if dev_l not in ("desktop", "mobile"):
            raise ValueError(f"Unsupported device: {dev}")
        if dev_l not in normalized:
            normalized.append(dev_l)
    return normalized


def _resolve_environment_name(environment: Optional[str]) -> str:
    return environment or cfg.get_current_environment()


def _read_dashboard_context(environment: Optional[str]) -> Dict[str, Any]:
    env_name = _resolve_environment_name(environment).upper()
    if "_" not in env_name:
        return {}
    project, env = env_name.split("_", 1)
    spreadsheet_id = os.getenv("GS_SHEET_ID")
    if not spreadsheet_id:
        return {}
    try:
        from services.google.google_sheets_client import GoogleSheetsClient
        creds_path = cfg.get_google_creds_path()
        context = GoogleSheetsClient.read_dashboard_sprint_context(str(creds_path), spreadsheet_id, project)
        context["project"] = project
        context["environment"] = env
        return context
    except Exception:
        _log_exception(f"Failed to read dashboard context for environment={environment}")
        return {}


def _resolve_sprint(sprint: Optional[str], environment: Optional[str] = None) -> str:
    if sprint:
        return sprint
    return str(_read_dashboard_context(environment).get("active_sprint") or "")


def _resolve_tag(tag: Optional[str], environment: Optional[str] = None) -> str:
    if tag:
        return tag
    dashboard_context = _read_dashboard_context(environment)
    if not dashboard_context.get("has_any_rollout"):
        return ""
    env_name = dashboard_context.get("environment") or ""
    rollout = dashboard_context.get("rollout") or {}
    return "after" if rollout.get(env_name) else "before"


def _resolve_launch_context(tag: Optional[str], sprint: Optional[str], environment: Optional[str]) -> tuple[str, str]:
    return _resolve_tag(tag, environment), _resolve_sprint(sprint, environment)


def _queue_lighthouse_job(routes: List[str], device: str, iterations: int, environment: Optional[str], tag: Optional[str], sprint: Optional[str]) -> str:
    job_id = _register_job(
        kind="lighthouse_cli",
        payload={"routes": routes, "device": device, "iterations": iterations, "environment": environment, "tag": tag, "sprint": sprint},
    )
    return job_id


def _queue_api_job(routes: List[str], device: str, iterations: int, environment: Optional[str], tag: Optional[str], sprint: Optional[str]) -> str:
    job_id = _register_job(
        kind="lighthouse_api",
        payload={"routes": routes, "device": device, "iterations": iterations, "environment": environment, "tag": tag, "sprint": sprint},
    )
    return job_id



def _ensure_jobs_state_dir() -> None:
    os.makedirs(os.path.dirname(JOBS_STATE_PATH), exist_ok=True)


def _load_jobs_state() -> Dict[str, Dict[str, Any]]:
    _ensure_jobs_state_dir()
    if not os.path.exists(JOBS_STATE_PATH):
        return {}
    try:
        with open(JOBS_STATE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except Exception:
        _log_exception("Failed to load jobs state")
        return {}


def _save_jobs_state(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_jobs_state_dir()
    tmp_path = f"{JOBS_STATE_PATH}.{os.getpid()}.tmp"
    for attempt in range(3):
        try:
            with open(tmp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(tmp_path, JOBS_STATE_PATH)
            return
        except PermissionError:
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
            else:
                _log_exception("Failed to save jobs state after retries")
        except Exception:
            _log_exception("Failed to save jobs state")
            break
    # Не падаем — job продолжит работу даже если state не сохранился
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def _prune_jobs_state(data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    now = time.time()
    items = sorted(
        data.items(),
        key=lambda item: item[1].get("created_at") or 0,
        reverse=True,
    )
    kept: Dict[str, Dict[str, Any]] = {}
    completed: List[tuple[str, Dict[str, Any]]] = []

    for job_id, job in items:
        status = job.get("status")
        ended_at = job.get("ended_at") or job.get("created_at") or now
        is_finished = status in {"done", "error"}
        if is_finished and (now - ended_at) > JOB_TTL_SECONDS:
            continue
        if is_finished:
            completed.append((job_id, job))
            continue
        kept[job_id] = job

    for job_id, job in completed[:MAX_JOBS_HISTORY]:
        kept[job_id] = job

    return dict(sorted(kept.items(), key=lambda item: item[1].get("created_at") or 0))


def _load_pruned_jobs_state() -> Dict[str, Dict[str, Any]]:
    jobs = _load_jobs_state()
    pruned = _prune_jobs_state(jobs)
    if pruned != jobs:
        _save_jobs_state(pruned)
    return pruned


def _update_job_state(job_id: str, **changes: Any) -> None:
    jobs = _load_pruned_jobs_state()
    if job_id not in jobs:
        return
    jobs[job_id].update(changes)
    _save_jobs_state(jobs)


def _spawn_job_process(job_id: str) -> None:
    command = [sys.executable, os.path.abspath(__file__), "--execute-job", job_id]
    kwargs: Dict[str, Any] = {
        "cwd": ROOT_DIR,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        kwargs["start_new_session"] = True
    _log_info(f"Spawning background job process for job_id={job_id}")
    subprocess.Popen(command, **kwargs)


def _execute_job(job_id: str) -> int:
    jobs = _load_pruned_jobs_state()
    job = jobs.get(job_id)
    if not job:
        _log_info(f"execute_job: job_id={job_id} not found")
        return 1
    _update_job_state(job_id, status="running", started_at=time.time(), ended_at=None, result=None, error=None)
    try:
        _log_info(f"execute_job: start job_id={job_id} kind={job.get('kind')}")
        result = _run_job(job["kind"], job.get("payload") or {})
        _update_job_state(job_id, status="done", ended_at=time.time(), result=result, error=None)
        _log_info(f"execute_job: done job_id={job_id}")
        return 0
    except Exception as e:  # noqa: BLE001
        _log_exception(f"execute_job: failed job_id={job_id}")
        _update_job_state(
            job_id,
            status="error",
            ended_at=time.time(),
            error=f"{e} | {traceback.format_exc(limit=2)}",
        )
        return 1


def _run_job(kind: str, payload: dict) -> str:
    if kind == "lighthouse_cli":
        return _run_lighthouse_job(payload)
    if kind == "lighthouse_api":
        return _run_api_job(payload)
    if kind == "crux":
        return _run_crux_job(payload)
    raise ValueError(f"Unknown job kind: {kind}")


def _format_summary(summary: dict, env_name: str, payload: dict, resolved_sprint: str, resolved_tag: str) -> str:
    succeeded = summary.get("succeeded", [])
    failed = summary.get("failed", [])
    parts = [
        f"done: env={env_name}, device={payload.get('device')}, routes={payload.get('routes')}, "
        f"iterations={payload.get('iterations')}, sprint={resolved_sprint or '—'}, tag={resolved_tag or '—'}",
        f"succeeded={len(succeeded)}/{len(succeeded) + len(failed)} routes: {succeeded}",
    ]
    if failed:
        parts.append(f"failed={len(failed)}: {failed}")
    return "\n".join(parts)


def _run_lighthouse_job(payload: dict) -> str:
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService
        env_name = _resolve_environment_name(payload.get("environment"))
        resolved_tag, resolved_sprint = _resolve_launch_context(payload.get("tag"), payload.get("sprint"), env_name)
        base_url = cfg.get_base_url(environment=env_name)
        service = SpeedtestService(environment=env_name)
        summary = service.run_local_tests(
            route_keys=payload.get("routes") or [],
            device_type=payload.get("device") or "desktop",
            n_iteration=int(payload.get("iterations") or DEFAULT_ITERATIONS),
            base_url=base_url,
            tag=resolved_tag,
            sprint=resolved_sprint,
        )
    return _format_summary(summary, env_name, payload, resolved_sprint, resolved_tag)


def _run_api_job(payload: dict) -> str:
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService
        env_name = _resolve_environment_name(payload.get("environment"))
        resolved_tag, resolved_sprint = _resolve_launch_context(payload.get("tag"), payload.get("sprint"), env_name)
        base_url = cfg.get_base_url(environment=env_name)
        service = SpeedtestService(environment=env_name)
        summary = service.run_api_aggregated_tests(
            route_keys=payload.get("routes") or [],
            device_type=payload.get("device") or "desktop",
            n_iteration=int(payload.get("iterations") or DEFAULT_ITERATIONS),
            base_url=base_url,
            tag=resolved_tag,
            sprint=resolved_sprint,
        )
    return _format_summary(summary, env_name, payload, resolved_sprint, resolved_tag)


def _run_crux_job(payload: dict) -> str:
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService
        env_name = _resolve_environment_name(payload.get("environment"))
        resolved_tag, resolved_sprint = _resolve_launch_context(payload.get("tag"), payload.get("sprint"), env_name)
        base_url = cfg.get_base_url(environment=env_name)
        service = SpeedtestService(environment=env_name)
        summary = service.run_crux_data_collection(
            route_keys=payload.get("routes") or [],
            device_type=payload.get("device") or "desktop",
            base_url=base_url,
            tag=resolved_tag,
            sprint=resolved_sprint,
        )
    return _format_summary(summary, env_name, payload, resolved_sprint, resolved_tag)


# ─── Мини-очередь заданий (fire-and-forget + статус) ─────────────────────────


def _register_job(kind: str, payload: dict) -> str:
    job_id = uuid.uuid4().hex[:8]
    jobs = _load_pruned_jobs_state()
    jobs[job_id] = {
        "kind": kind,
        "payload": payload,
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "ended_at": None,
        "result": None,
        "error": None,
    }
    _save_jobs_state(jobs)
    _log_info(f"register_job: job_id={job_id} kind={kind} payload={payload}")
    _spawn_job_process(job_id)
    return job_id


# ─── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def run_lighthouse(
    routes: List[str],
    device: str,
    iterations: int = 10,
    environment: Optional[str] = None,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Запускает Lighthouse CLI для указанных роутов.

    Переключает контур (если указан), прогоняет N итераций,
    агрегирует результаты и записывает в Google Sheets.
    Если sprint/tag не переданы явно, они берутся из dashboard.

    Args:
        routes: Список ключей роутов из routes.ini (например ["home", "login"]).
        device: Тип устройства — "desktop" или "mobile".
        iterations: Количество итераций (по умолчанию 10).
        environment: Контур (например "VRP_DEV"). Если не указан — используется текущий.
    """
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService

        env_name = _resolve_environment_name(environment)
        resolved_tag = _resolve_tag(tag, env_name)
        resolved_sprint = _resolve_sprint(sprint, environment)
        base_url = cfg.get_base_url(environment=env_name)

        service = SpeedtestService(environment=env_name)
        service.run_local_tests(
            route_keys=routes,
            device_type=device,
            n_iteration=iterations,
            base_url=base_url,
            tag=resolved_tag,
            sprint=resolved_sprint,
        )

    return (
        f"Lighthouse CLI завершён.\n"
        f"Контур: {env_name} ({base_url})\n"
        f"Роуты: {', '.join(routes)}\n"
        f"Устройство: {device}\n"
        f"Итераций: {iterations}\n"
        f"Спринт: {resolved_sprint or '—'}\n"
        f"Тег: {resolved_tag or '—'}\n"
        f"Результаты записаны в Google Sheets."
    )


@mcp.tool()
def run_crux(
    routes: List[str],
    device: str,
    environment: Optional[str] = None,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Собирает CrUX данные (Chrome User Experience Report) для указанных роутов.

    CrUX доступен только для PROD-контуров (*_PROD).
    Если sprint/tag не переданы явно, они берутся из dashboard.

    Args:
        routes: Список ключей роутов из routes.ini.
        device: Тип устройства — "desktop" или "mobile".
        environment: Контур (рекомендуется *_PROD). Если не указан — текущий.
    """
    with _suppress_stdout():
        from services.lighthouse.pagespeed_service import SpeedtestService

        env_name = _resolve_environment_name(environment)
        resolved_tag = _resolve_tag(tag, env_name)
        resolved_sprint = _resolve_sprint(sprint, environment)
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
            tag=resolved_tag,
            sprint=resolved_sprint,
        )

    return (
        f"CrUX сбор завершён.\n"
        f"Контур: {env_name} ({base_url})\n"
        f"Роуты: {', '.join(routes)}\n"
        f"Устройство: {device}\n"
        f"Спринт: {resolved_sprint or '—'}\n"
        f"Тег: {resolved_tag or '—'}\n"
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
def enqueue_lighthouse(
    routes: List[str],
    device: str,
    iterations: int = 5,
    environment: Optional[str] = None,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Добавляет задание на Lighthouse CLI в очередь и сразу возвращает job_id.

    Если sprint/tag не переданы явно, они берутся из dashboard.
    """

    job_id = _queue_lighthouse_job(
        routes=routes,
        device=device,
        iterations=iterations,
        environment=environment,
        tag=tag,
        sprint=sprint,
    )
    return f"job_id={job_id} (lighthouse_cli queued)"


@mcp.tool()
def enqueue_environment_saturation(
    environment: Optional[str] = None,
    routes: Optional[List[str]] = None,
    devices: Optional[List[str]] = None,
    iterations: int = DEFAULT_ITERATIONS,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Запускает серию прогонов для всех указанных маршрутов и устройств.

    Если sprint/tag не переданы явно, они берутся из dashboard.
    """

    resolved_routes = _resolve_routes(routes)
    resolved_devices = _resolve_devices(devices)
    iterations = max(iterations, DEFAULT_ITERATIONS)

    job_ids = []
    for device in resolved_devices:
        job_id = _queue_lighthouse_job(
            routes=resolved_routes,
            device=device,
            iterations=iterations,
            environment=environment,
            tag=tag,
            sprint=sprint,
        )
        job_ids.append(job_id)

    return (
        f"Сатурация запланирована: среда={environment or cfg.get_current_environment()}, "
        f"роуты=[{', '.join(resolved_routes)}], устройства=[{', '.join(resolved_devices)}], "
        f"итераций={iterations}. Job ID: {', '.join(job_ids)}"
    )


@mcp.tool()
def enqueue_api(
    routes: List[str],
    device: str,
    iterations: int = 5,
    environment: Optional[str] = None,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Добавляет задание на Lighthouse API в очередь и сразу возвращает job_id.

    Если sprint/tag не переданы явно, они берутся из dashboard.
    """

    job_id = _queue_api_job(
        routes=routes,
        device=device,
        iterations=iterations,
        environment=environment,
        tag=tag,
        sprint=sprint,
    )
    return f"job_id={job_id} (lighthouse_api queued)"


@mcp.tool()
def enqueue_api_saturation(
    environment: Optional[str] = None,
    routes: Optional[List[str]] = None,
    devices: Optional[List[str]] = None,
    iterations: int = DEFAULT_ITERATIONS,
    tag: Optional[str] = None,
    sprint: Optional[str] = None,
) -> str:
    """Запускает серию API-прогонов для всех указанных маршрутов и устройств.

    Если sprint/tag не переданы явно, они берутся из dashboard.
    """

    resolved_routes = _resolve_routes(routes)
    resolved_devices = _resolve_devices(devices)
    iterations = max(iterations, DEFAULT_ITERATIONS)
    job_ids = []
    for device in resolved_devices:
        job_id = _queue_api_job(
            routes=resolved_routes,
            device=device,
            iterations=iterations,
            environment=environment,
            tag=tag,
            sprint=sprint,
        )
        job_ids.append(job_id)

    return (
        f"API-сатурация запланирована: среда={environment or cfg.get_current_environment()}, "
        f"роуты=[{', '.join(resolved_routes)}], устройства=[{', '.join(resolved_devices)}], "
        f"итераций={iterations}. Job ID: {', '.join(job_ids)}"
    )


@mcp.tool()
def enqueue_crux(routes: List[str], device: str, environment: Optional[str] = None, tag: Optional[str] = None, sprint: Optional[str] = None) -> str:
    """Добавляет задание на CrUX сбор в очередь и возвращает job_id.

    Если sprint/tag не переданы явно, они берутся из dashboard.
    """

    job_id = _register_job(
        kind="crux",
        payload={"routes": routes, "device": device, "environment": environment, "tag": tag, "sprint": sprint},
    )
    return f"job_id={job_id} (crux queued)"


@mcp.tool()
def list_jobs() -> str:
    """Возвращает краткий статус по всем заданиям в очереди."""
    jobs = _load_pruned_jobs_state()
    if not jobs:
        return "Очередь пуста."
    lines = [_format_job(jid, data) for jid, data in jobs.items()]
    return "\n".join(lines)


@mcp.tool()
def job_status(job_id: str) -> str:
    """Возвращает статус конкретного задания."""
    jobs = _load_pruned_jobs_state()
    data = jobs.get(job_id)
    if not data:
        return f"Задание {job_id} не найдено."
    details = _format_job(job_id, data)
    result = data.get("result")
    error = data.get("error")
    if result:
        details += f"\nresult={result}"
    if error:
        details += f"\nerror={error}"
    return details


if __name__ == "__main__":
    try:
        _log_info("mcp_server main started")
        parser = argparse.ArgumentParser(description="Lighthouse MCP helper / server")
        parser.add_argument("--tool", choices=["run_lighthouse", "run_crux"], help="Запустить tool и выйти")
        parser.add_argument("--routes", nargs="+", help="Ключи роутов из routes.ini")
        parser.add_argument("--device", choices=["desktop", "mobile"], help="Тип устройства")
        parser.add_argument("--iterations", type=int, default=10, help="Количество итераций (для run_lighthouse)")
        parser.add_argument("--tag", help="Необязательный tag override. Без него tag считается по rollout в dashboard")
        parser.add_argument("--sprint", help="Необязательный sprint override. Без него sprint берётся из Sprint Control в dashboard")
        parser.add_argument("--environment", help="Контур (VRP_PROD и т.д.)")
        parser.add_argument("--execute-job", help="Выполнить задание очереди по job_id и выйти")
        parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio", help="Транспорт MCP: stdio (default) или streamable-http")
        args, _ = parser.parse_known_args()

        _log_info(f"parsed args: tool={args.tool} execute_job={args.execute_job} transport={args.transport}")

        if args.execute_job:
            sys.exit(_execute_job(args.execute_job))

        if args.tool:
            if not args.routes or not args.device:
                parser.error("--routes и --device обязательны при --tool")
            if args.tool == "run_lighthouse":
                print(run_lighthouse(args.routes, args.device, args.iterations, args.environment, tag=args.tag, sprint=args.sprint))
            else:
                print(run_crux(args.routes, args.device, args.environment, tag=args.tag, sprint=args.sprint))
            sys.exit(0)

        sys.stdout = _real_stdout
        _log_info(f"starting FastMCP transport={args.transport}")
        mcp.run(transport=args.transport)
    except Exception:
        _log_exception("Fatal error in mcp_server main")
        print("Fatal error in mcp_server. See log file for details.", file=sys.stderr)
        sys.exit(1)




