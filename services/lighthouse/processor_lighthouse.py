"""
Модуль для обработки результатов тестов скорости Lighthouse.
- Парсинг JSON-файлов
- Агрегация метрик
- Запись результатов в Google Sheets
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from services.lighthouse.configs.config_lighthouse import (
    TEMP_REPORTS_DIR,
    get_current_environment,
    get_full_url,
    resolve_worksheet_name,
    cleanup_temp_files,
)
from services.google.google_sheets_client import GoogleSheetsClient


def parse_lighthouse_results(json_file: str) -> Optional[dict]:
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        return {
            "P": data["categories"]["performance"]["score"] * 100,
            "LCP": data["audits"]["largest-contentful-paint"]["numericValue"],
            "FCP": data["audits"]["first-contentful-paint"]["numericValue"],
            "TBT": data["audits"]["total-blocking-time"]["numericValue"],
            "CLS": data["audits"]["cumulative-layout-shift"]["numericValue"],
            "SI": data["audits"]["speed-index"]["numericValue"],
            "TTI": data["audits"]["interactive"]["numericValue"],
            "TTFB": data["audits"]["server-response-time"]["numericValue"],
            "INP": data.get("audits", {}).get("experimental-interaction-to-next-paint", {}).get("numericValue", 0),
        }
    except Exception as e:
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
            "LCP_good_pct": round(metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("distributions", [{}])[0].get("proportion", 0) * 100, 2),
            "FCP_good_pct": round(metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("distributions", [{}])[0].get("proportion", 0) * 100, 2),
            "INP_good_pct": round(metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("distributions", [{}])[0].get("proportion", 0) * 100, 2),
            "CLS_good_pct": round(metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("distributions", [{}])[0].get("proportion", 0) * 100, 2),
            "TTFB": metrics.get("EXPERIMENTAL_TIME_TO_FIRST_BYTE", {}).get("percentile", 0)
        }
    except Exception as e:
        print(f"[!] Ошибка при разборе файла {json_file}: {e}")
        return None


def aggregate_results(results: List[Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        raise ValueError("[!] Нет валидных результатов для агрегации.")

    aggregated = {}
    for metric in valid_results[0].keys():
        values = [res[metric] for res in valid_results if metric in res]
        aggregated[metric] = {
            "min": round(np.min(values), 2),
            "max": round(np.max(values), 2),
            "avg": round(np.mean(values), 2),
            "p90": round(np.percentile(values, 90), 2)
        }
    return aggregated


def flatten_aggregated_metrics(aggregated: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    return {f"{metric}_{stat}": value for metric, stats in aggregated.items() for stat, value in stats.items()}


def build_row(timestamp: str, project_code: str, full_url: str, route_key: str,
              device_type: str, aggregated: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    row = {
        "Date": timestamp,
        "Sprint": "",
        "Env": project_code,
        "Route": GoogleSheetsClient.prepare_link(route_key, full_url),
        "Device": device_type,
    }
    row.update(flatten_aggregated_metrics(aggregated))
    return row


def process_and_save_results(json_paths: List[str], route_key: str, device_type: str,
                             gsheet_client: GoogleSheetsClient,
                             is_local: bool = True,
                             keep_temp_files: bool = False):
    parsed_results = [parse_lighthouse_results(p) for p in json_paths]
    if not parsed_results or all(res is None for res in parsed_results):
        print(f"[WARNING!] Нет валидных данных для роута {route_key}.")
        return
    aggregated = aggregate_results(parsed_results)

    if not keep_temp_files:
        cleanup_temp_files(TEMP_REPORTS_DIR)

    environment = get_current_environment()
    source_type = "cli" if is_local else "api"
    worksheet_name = resolve_worksheet_name(environment, source=source_type)
    template_name = "_CLI_Template" if source_type == "cli" else "_API_Template"

    gsheet_client.worksheet_name = worksheet_name
    gsheet_client.ensure_sheet_exists(sheet_name=worksheet_name, source=source_type)

    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    row = build_row(
        timestamp=timestamp,
        project_code=f"VRS-{environment}",
        full_url=get_full_url(route_key),
        route_key=route_key,
        device_type=device_type,
        aggregated=aggregated
    )
    gsheet_client.append_result(row)


def process_crux_results(crux_file: str, route_key: str, device: str,
                         gsheet_client: GoogleSheetsClient):
    crux_metrics = parse_crux_results(crux_file)
    if not crux_metrics:
        print(f"[WARNING!] Нет данных для роута {route_key}.")
        return

    source_type = "crux"
    environment = get_current_environment()
    worksheet_name = resolve_worksheet_name(environment, source=source_type)
    gsheet_client.worksheet_name = worksheet_name
    gsheet_client.ensure_sheet_exists(sheet_name=worksheet_name, source=source_type)

    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    row = {
        "Date": timestamp,
        "Sprint": "",
        "Env": f"VRS-{environment}",
        "Route": GoogleSheetsClient.prepare_link(route_key, get_full_url(route_key)),
        "Device": device,
        **crux_metrics
        # ToDo: нужно Добавить обработку других метрик!!!!!!!!!!
    }
    gsheet_client.append_result(row)