"""
Обработка результатов Lighthouse/CrUX:
- разбор JSON
- агрегация метрик (p75/p90 + min/max/avg + iterations)
- запись в Google Sheets
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from services.google.google_sheets_client import GoogleSheetsClient
from services.lighthouse.configs.config_lighthouse import (
    TEMP_REPORTS_DIR,
    cleanup_temp_files,
    get_current_environment,
    get_full_url,
    resolve_worksheet_name,
)


def _split_environment(environment: str) -> tuple[str, str]:
    env_value = (environment or '').upper()
    if '_' in env_value:
        project, env = env_value.split('_', 1)
        return project, env
    return env_value, ''


def _format_env_label(environment: str) -> str:
    """VRP_PROD → VRP [PROD], VRS_DEV → VRS [DEV]."""
    project, env = _split_environment(environment)
    return f"{project} [{env}]" if env else project


def parse_lighthouse_results(json_file: str) -> Optional[dict]:
    """
    Парсит JSON Lighthouse и нормализует метрики.

    Все временные метрики → миллисекунды.
    CLS остаётся безразмерным (0..1).
    """
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        lcp_raw = data["audits"]["largest-contentful-paint"]["numericValue"]
        # Защита от секунд: если значение выглядит как секунды (<50), умножаем.
        lcp_ms = lcp_raw * 1000 if lcp_raw < 50 else lcp_raw
        lcp_ms = int(round(lcp_ms))

        inp_val = data.get("audits", {}).get("experimental-interaction-to-next-paint", {}).get("numericValue")
        if inp_val is None:
            inp_val = data.get("audits", {}).get("max-potential-fid", {}).get("numericValue", 0)
        inp_ms = int(round(inp_val))

        return {
            "P": int(data["categories"]["performance"]["score"] * 100),
            "LCP": lcp_ms,
            "FCP": int(round(data["audits"]["first-contentful-paint"]["numericValue"])),
            "TBT": int(round(data["audits"]["total-blocking-time"]["numericValue"])),
            "CLS": round(data["audits"]["cumulative-layout-shift"]["numericValue"], 4),
            "SI": int(round(data["audits"]["speed-index"]["numericValue"])),
            "TTI": int(round(data["audits"]["interactive"]["numericValue"])),
            "TTFB": int(round(data["audits"]["server-response-time"]["numericValue"])),
            "INP": inp_ms,
        }

    except Exception as e:  # pragma: no cover - логирование
        print(f"[!] Ошибка при разборе файла {json_file}: {e}")
        return None


def parse_crux_results(json_file: str) -> Optional[Dict[str, Any]]:
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        metrics = data.get("metrics", {}) or data.get("loadingExperience", {}).get("metrics", {})

        return {
            "LCP_p75": metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0),
            "FCP_p75": metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0),
            "INP_p75": metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile", 0),
            "CLS_p75": metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", 0),
            "LCP_good_pct": round(
                metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("distributions", [{}])[0].get("proportion", 0) * 100,
                2,
            ),
            "FCP_good_pct": round(
                metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("distributions", [{}])[0].get("proportion", 0) * 100, 2
            ),
            "INP_good_pct": round(
                metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("distributions", [{}])[0].get("proportion", 0) * 100,
                2,
            ),
            "CLS_good_pct": round(
                metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("distributions", [{}])[0].get("proportion", 0)
                * 100,
                2,
            ),
            "TTFB": metrics.get("EXPERIMENTAL_TIME_TO_FIRST_BYTE", {}).get("percentile", 0),
        }

    except Exception as e:  # pragma: no cover - логирование
        print(f"[!] Ошибка при разборе файла {json_file}: {e}")
        return None


def _safe_clean(values: List[float]) -> List[float]:
    """Убираем None/NaN/нулевые и приводим к float."""
    cleaned = []
    for v in values:
        try:
            num = float(v)
        except (TypeError, ValueError):
            continue
        if np.isnan(num) or num <= 0:
            continue
        cleaned.append(num)
    return cleaned


def aggregate_results(results: List[Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
    """
    Аггрегирует результаты Lighthouse:
    - Core Web Vitals: p75, p90
    - Остальные: p75
    """
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        raise ValueError("[!] Нет валидных результатов для агрегации.")

    core_web_vitals = {"LCP", "INP", "CLS"}

    aggregated: Dict[str, Dict[str, float]] = {}
    for metric in valid_results[0].keys():
        raw_values = [res.get(metric) for res in valid_results if isinstance(res.get(metric), (int, float))]
        values = _safe_clean(raw_values)
        if not values:
            continue

        decimals = 4 if metric == "CLS" else 0

        stats: Dict[str, float] = {}

        if metric in core_web_vitals:
            stats["p75"] = round(float(np.percentile(values, 75)), decimals)
            stats["p90"] = round(float(np.percentile(values, 90)), decimals)
        else:
            stats["p75"] = round(float(np.percentile(values, 75)), decimals)

        aggregated[metric] = stats

    return aggregated


def flatten_aggregated_metrics(aggregated: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Плоский словарь для записи в Sheet.
    Порядок ключей согласован с DEFAULT_HEADERS.
    """
    ordered_result: Dict[str, float] = {}

    if "P" in aggregated:
        ordered_result["P"] = aggregated["P"]["p75"]

    for metric in ["LCP", "INP", "CLS"]:
        if metric in aggregated:
            ordered_result[metric] = aggregated[metric]["p75"]
    for metric in ["LCP", "INP", "CLS"]:
        if metric in aggregated:
            ordered_result[f"{metric}_p90"] = aggregated[metric]["p90"]

    for metric in ["TBT", "FCP", "SI", "TTI", "TTFB"]:
        if metric in aggregated:
            ordered_result[metric] = aggregated[metric]["p75"]

    return ordered_result


def build_row(
    timestamp: str,
    source: str,
    iterations: int,
    environment: str,
    route_key: str,
    device_type: str,
    aggregated: Dict[str, Dict[str, float]],
    full_url: str = None,
    run_id: str = None,
    tag: str = "",
    sprint: str = "",
) -> Dict[str, Any]:
    """
    Формирует строку для Google Sheets.
    """
    source_type = f"{source.upper()}{{{iterations}}}"
    device_label = "desktop" if device_type.lower() == "desktop" else "mobile"
    page_link = GoogleSheetsClient.prepare_link(route_key, full_url) if full_url else route_key
    if run_id is None:
        now = datetime.now()
        run_id = now.strftime("%Y.%m.%d-%H%M%S")

    project, env = _split_environment(environment)

    row = {
        "date": timestamp,
        "project": project,
        "environment": env or environment,
        "source": source.upper(),
        "sprint": sprint or "",
        "run_id": run_id,
        "tag": tag,
        "type": source_type,
        "page": page_link,
        "device": device_label,
        "iterations": iterations,
    }
    row.update(flatten_aggregated_metrics(aggregated))
    return row


def process_and_save_results(
    json_paths: List[str],
    route_key: str,
    device_type: str,
    gsheet_client: GoogleSheetsClient,
    is_local: bool = True,
    keep_temp_files: bool = False,
    environment: Optional[str] = None,
    full_url: Optional[str] = None,
    iterations: int = 10,
    run_id: Optional[str] = None,
    tag: str = "",
    sprint: str = "",
):
    parsed_results = [parse_lighthouse_results(p) for p in json_paths]

    if not parsed_results or all(res is None for res in parsed_results):
        print(f"[WARNING!] Нет валидных данных для роутa {route_key}.")
        return

    aggregated = aggregate_results(parsed_results)

    if not keep_temp_files:
        temp_dirs = {Path(p).parent for p in json_paths}
        for temp_dir in temp_dirs:
            try:
                temp_dir.relative_to(TEMP_REPORTS_DIR)
            except ValueError:
                continue
            cleanup_temp_files(temp_dir)

    environment = environment or get_current_environment()
    resolved_url = full_url or get_full_url(route_key)

    source_type = "cli" if is_local else "api"
    worksheet_name = resolve_worksheet_name(environment, source=source_type)

    gsheet_client.worksheet_name = worksheet_name
    gsheet_client.ensure_sheet_exists(sheet_name=worksheet_name, source=source_type)

    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    row = build_row(
        timestamp=timestamp,
        source=source_type.upper(),
        iterations=iterations,
        environment=environment,
        route_key=route_key,
        device_type=device_type,
        aggregated=aggregated,
        full_url=resolved_url,
        run_id=run_id,
        tag=tag,
        sprint=sprint,
    )
    gsheet_client.append_result(row)


def process_crux_results(
    crux_file: str,
    route_key: str,
    device: str,
    gsheet_client: GoogleSheetsClient,
    full_url_override: str = None,
    route_label: str = None,
    environment: Optional[str] = None,
    run_id: Optional[str] = None,
    tag: str = "",
    sprint: str = "",
):
    crux_metrics = parse_crux_results(crux_file)

    if not crux_metrics:
        print(f"[WARNING!] Нет данных для роутa {route_key}.")
        return

    source_type = "crux"
    environment = environment or get_current_environment()
    worksheet_name = resolve_worksheet_name(environment, source=source_type)

    gsheet_client.worksheet_name = worksheet_name
    gsheet_client.ensure_sheet_exists(sheet_name=worksheet_name, source=source_type)

    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    target_url = full_url_override or get_full_url(route_key)
    link_label = route_label or route_key
    project, env = _split_environment(environment)
    row = {
        "date": timestamp,
        "project": project,
        "environment": env or environment,
        "source": "CRUX",
        "sprint": sprint or "",
        "run_id": run_id or datetime.now().strftime("%Y.%m.%d-%H%M%S"),
        "tag": tag or "",
        "type": "CRUX{1}",
        "page": GoogleSheetsClient.prepare_link(link_label, target_url),
        "device": device,
        "iterations": 1,
        "LCP": crux_metrics.get("LCP_p75"),
        "FCP": crux_metrics.get("FCP_p75"),
        "INP": crux_metrics.get("INP_p75"),
        "CLS": crux_metrics.get("CLS_p75"),
        "LCP_good_pct": crux_metrics.get("LCP_good_pct"),
        "FCP_good_pct": crux_metrics.get("FCP_good_pct"),
        "INP_good_pct": crux_metrics.get("INP_good_pct"),
        "CLS_good_pct": crux_metrics.get("CLS_good_pct"),
        "TTFB": crux_metrics.get("TTFB"),
    }

    gsheet_client.append_result(row)
