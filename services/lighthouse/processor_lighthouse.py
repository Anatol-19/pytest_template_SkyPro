"""

Модуль для обработки результатов тестов скорости Lighthouse.

- Парсинг JSON-файлов

- Агрегация метрик

- Запись результатов в Google Sheets

"""

import json
from pathlib import Path

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

def _format_env_label(environment: str) -> str:
    """Возвращает метку окружения: VRP_PROD → VRP [PROD], VRS_DEV → VRS [DEV]."""
    if "_" in environment:
        project, env = environment.split("_", 1)
        return f"{project} [{env}]"
    return environment

def parse_lighthouse_results(json_file: str) -> Optional[dict]:
    """
    Парсит JSON-отчёт Lighthouse и возвращает метрики.
    
    Единицы измерения:
    - LCP: секунды (с 2 знаками)
    - INP: миллисекунды (целые)
    - CLS: безразмерная (4 знака)
    - TBT: миллисекунды (целые)
    - FCP: миллисекунды (целые)
    - SI: миллисекунды (целые)
    - TTI: миллисекунды (целые)
    - TTFB: миллисекунды (целые)
    - P: проценты (целые)
    """
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # LCP: ms -> секунды (2 знака)
        lcp_ms = data["audits"]["largest-contentful-paint"]["numericValue"]
        lcp_sec = round(lcp_ms / 1000, 2)
        
        # INP: может отсутствовать, берём из max-potential-fid как fallback
        inp_val = data.get("audits", {}).get("experimental-interaction-to-next-paint", {}).get("numericValue")
        if inp_val is None:
            # Fallback: max-potential-fid или 0
            inp_val = data.get("audits", {}).get("max-potential-fid", {}).get("numericValue", 0)
        inp_ms = int(round(inp_val))

        return {
            "P": int(data["categories"]["performance"]["score"] * 100),
            "LCP": lcp_sec,
            "FCP": int(round(data["audits"]["first-contentful-paint"]["numericValue"])),
            "TBT": int(round(data["audits"]["total-blocking-time"]["numericValue"])),
            "CLS": round(data["audits"]["cumulative-layout-shift"]["numericValue"], 4),
            "SI": int(round(data["audits"]["speed-index"]["numericValue"])),
            "TTI": int(round(data["audits"]["interactive"]["numericValue"])),
            "TTFB": int(round(data["audits"]["server-response-time"]["numericValue"])),
            "INP": inp_ms,
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
    """
    Агрегирует результаты Lighthouse запусков.
    
    Core Web Vitals (LCP, INP, CLS): p75, p90
    Остальные метрики: только p75
    
    Единицы:
    - LCP: секунды (агрегируем как секунды)
    - INP: миллисекунды (целые)
    - CLS: безразмерная
    - Остальные: миллисекунды (целые)
    """
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        raise ValueError("[!] Нет валидных результатов для агрегации.")
    
    core_web_vitals = {"LCP", "INP", "CLS"}
    time_metrics_ms = {"FCP", "TBT", "SI", "TTI", "TTFB"}  # в миллисекундах
    
    aggregated = {}
    for metric in valid_results[0].keys():
        values = [res[metric] for res in valid_results if metric in res and isinstance(res.get(metric), (int, float))]
        
        if not values:
            continue
        
        if metric == "CLS":
            # CLS: 4 знака
            decimals = 4
        elif metric == "LCP":
            # LCP: секунды, 2 знака
            decimals = 2
        elif metric == "TBT":
            # TBT: целые
            decimals = 0
        else:
            decimals = 0
        
        if metric in core_web_vitals:
            aggregated[metric] = {
                "p75": round(np.percentile(values, 75), decimals),
                "p90": round(np.percentile(values, 90), decimals)
            }
        else:
            aggregated[metric] = {
                "p75": round(np.percentile(values, 75), decimals)
            }
    
    return aggregated

def flatten_aggregated_metrics(aggregated: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Преобразует агрегированные метрики в плоский словарь.
    
    Порядок ключей соответствует mapping Google Sheets:
    P, LCP, INP, CLS, LCP_p90, INP_p90, CLS_p90, TBT, FCP, SI, TTI, TTFB
    """
    core_web_vitals = {"LCP", "INP", "CLS"}
    
    # Явный порядок метрик
    ordered_result = {}
    
    # P (Performance score) — если есть
    if "P" in aggregated:
        ordered_result["P"] = aggregated["P"]["p75"]
    
    # Core Web Vitals: p75 затем p90 для каждой
    for metric in ["LCP", "INP", "CLS"]:
        if metric in aggregated:
            ordered_result[metric] = aggregated[metric]["p75"]
    
    for metric in ["LCP", "INP", "CLS"]:
        if metric in aggregated:
            ordered_result[f"{metric}_p90"] = aggregated[metric]["p90"]
    
    # Остальные метрики в заданном порядке
    for metric in ["TBT", "FCP", "SI", "TTI", "TTFB"]:
        if metric in aggregated:
            ordered_result[metric] = aggregated[metric]["p75"]
    
    return ordered_result

def build_row(timestamp: str, source: str, iterations: int, environment: str, route_key: str,
              device_type: str, aggregated: Dict[str, Dict[str, float]], full_url: str = None,
              run_id: str = None, tag: str = "") -> Dict[str, Any]:
    """
    Строит строку для записи в Google Sheets.
    
    Структура:
    - date, run_id, tag, type, page, device
    - P, LCP, INP, CLS, LCP_p90, INP_p90, CLS_p90
    - TBT, FCP, SI, TTI, TTFB
    """
    # Тип проверки (CLI{10} / API{10})
    source_type = f"{source.upper()}{{{iterations}}}"
    
    # Тип устройства
    device_label = "desktop" if device_type.lower() == "desktop" else "mobile"
    
    # Страница (route)
    page_link = GoogleSheetsClient.prepare_link(route_key, full_url) if full_url else route_key
    
    # Генерация run_id если не передан
    if run_id is None:
        date_part = timestamp.split()[0].replace(".", ".")
        run_id = f"{date_part}-1"
    
    row = {
        "date": timestamp.split()[0] if " " in timestamp else timestamp,
        "run_id": run_id,
        "tag": tag,
        "type": source_type,
        "page": page_link,
        "device": device_label,
    }
    
    # Добавляем метрики
    row.update(flatten_aggregated_metrics(aggregated))
    
    return row

def process_and_save_results(json_paths: List[str], route_key: str, device_type: str,
                             gsheet_client: GoogleSheetsClient,
                             is_local: bool = True,
                             keep_temp_files: bool = False,
                             environment: Optional[str] = None,
                             full_url: Optional[str] = None,
                             iterations: int = 10,
                             run_id: Optional[str] = None,
                             tag: str = ""):

    parsed_results = [parse_lighthouse_results(p) for p in json_paths]

    if not parsed_results or all(res is None for res in parsed_results):
        print(f"[WARNING!] Нет валидных данных для роута {route_key}.")
        return

    aggregated = aggregate_results(parsed_results)

    if not keep_temp_files:
        # Чистим только временные каталоги, созданные для текущего прогона,
        # чтобы параллельные задания не удаляли чужие файлы.
        temp_dirs = {Path(p).parent for p in json_paths}
        for temp_dir in temp_dirs:
            # Доп. защита: удаляем только подпапки внутри TEMP_REPORTS_DIR
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
        tag=tag
    )
    gsheet_client.append_result(row)

def process_crux_results(crux_file: str, route_key: str, device: str,
                         gsheet_client: GoogleSheetsClient,
                         full_url_override: str = None,
                         route_label: str = None,
                         environment: Optional[str] = None):

    crux_metrics = parse_crux_results(crux_file)

    if not crux_metrics:
        print(f"[WARNING!] Нет данных для роута {route_key}.")
        return

    source_type = "crux"
    environment = environment or get_current_environment()
    worksheet_name = resolve_worksheet_name(environment, source=source_type)

    gsheet_client.worksheet_name = worksheet_name

    gsheet_client.ensure_sheet_exists(sheet_name=worksheet_name, source=source_type)

    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    target_url = full_url_override or get_full_url(route_key)
    link_label = route_label or route_key
    row = {
        "date": timestamp.split()[0],
        "project": _format_env_label(environment),
        "sprint": "",
        "page": GoogleSheetsClient.prepare_link(link_label, target_url),
        "device": device,
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
