"""
Модуль для обработки результатов тестов скорости Lighthouse.
Отвечает за:
    - Парсинг JSON-файлов
    - Агрегацию метрик
    - Сохранение результатов в CSV
    - Запись результатов в Google Sheets
"""

import json
import os
import csv
from datetime import datetime
from typing import List
import numpy as np

from services.lighthouse.configs.config_lighthouse import REPORTS_DIR, get_current_environment, get_full_url, \
    get_worksheet_name, cleanup_temp_files, TEMP_REPORTS_DIR


def parse_lighthouse_results(json_file: str, include_extended_metrics: bool = False) -> dict | None:
    """
    Парсит JSON-отчет Lighthouse и извлекает ключевые метрики.
    Возвращает None при ошибке.
    :param json_file: Путь к JSON-файлу отчета Lighthouse.
    :param include_extended_metrics: Флаг для включения расширенных метрик.
    :return: Словарь с ключевыми метриками.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Базовые метрики
        result = {
            "performance": data["categories"]["performance"]["score"] * 100,
            "lcp": data["audits"]["largest-contentful-paint"]["numericValue"],
            "fcp": data["audits"]["first-contentful-paint"]["numericValue"],
            "tbt": data["audits"]["total-blocking-time"]["numericValue"],
            "cls": data["audits"]["cumulative-layout-shift"]["numericValue"],
            "si": data["audits"]["speed-index"]["numericValue"],
            "tti": data["audits"]["interactive"]["numericValue"]
        }

        # Расширенные метрики (если включены)
        if include_extended_metrics:
            result.update({
                "fmp": data["audits"].get("first-meaningful-paint", {}).get("numericValue", 0),
                "estimated_input_latency": data["audits"].get("estimated-input-latency", {}).get("numericValue", 0),
                "server_response_time": data["audits"].get("server-response-time", {}).get("numericValue", 0),
                "resource_sizes": {
                    "js": data["audits"].get("resource-summary", {}).get("details", {}).get("items", [{}])[0].get("size", 0),
                    "css": data["audits"].get("resource-summary", {}).get("details", {}).get("items", [{}])[1].get("size", 0),
                    "images": data["audits"].get("resource-summary", {}).get("details", {}).get("items", [{}])[2].get("size", 0)
                },
                "http_requests": data["audits"].get("network-requests", {}).get("details", {}).get("items", []),
                "blocking_resources": data["audits"].get("render-blocking-resources", {}).get("details", {}).get("items", []),
                "time_spent": {
                    "parsing": data["audits"].get("mainthread-work-breakdown", {}).get("details", {}).get("items", [{}])[0].get("duration", 0),
                    "scripting": data["audits"].get("mainthread-work-breakdown", {}).get("details", {}).get("items", [{}])[1].get("duration", 0),
                    "rendering": data["audits"].get("mainthread-work-breakdown", {}).get("details", {}).get("items", [{}])[2].get("duration", 0)
                },
                "categories": {
                    "seo": data["categories"]["seo"]["score"] * 100,
                    "best_practices": data["categories"]["best-practices"]["score"] * 100,
                    "accessibility": data["categories"]["accessibility"]["score"] * 100,
                    "pwa": data["categories"]["pwa"]["score"] * 100
                }
            })

        return result
    except Exception as e:
        print(f"[!] Ошибка при разборе файла {json_file}: {e}")
        return None


def parse_crux_results(json_file: str) -> dict | None:
    """
    Парсит JSON-отчет CrUX и извлекает ключевые метрики.
    Возвращает None при ошибке.
    :param json_file: Путь к JSON-файлу отчета CrUX.
    :return: Словарь с ключевыми метриками.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Извлекаем метрики из CrUX данных
        metrics = data.get("loadingExperience", {}).get("metrics", {})
        return {
            "LCP": metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0),
            "FID": metrics.get("FIRST_INPUT_DELAY_MS", {}).get("percentile", 0),
            "CLS": metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", 0),
            "FCP": metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0),
            "TTFB": metrics.get("TIME_TO_FIRST_BYTE", {}).get("percentile", 0)
        }
    except Exception as e:
        print(f"[!] Ошибка при разборе файла {json_file}: {e}")
        return None


def aggregate_results(results: list) -> dict:
    """
    Агрегирует результаты: min, max, среднее и 90-й процентиль.
    :param results: Список словарей с результатами тестов.
    :return: Словарь с агрегированными результатами.
    """
    results = [r for r in results if r is not None]
    if not results:
        raise ValueError("[!] Нет валидных результатов для агрегации.")


    aggregated = {}
    for metric in results[0].keys():
        values = [res[metric] for res in results]
        aggregated[metric] = {
            "min": round(np.min(values), 2),
            "max": round(np.max(values), 2),
            "mean": round(np.mean(values), 2),
            "p90": round(np.percentile(values, 90), 2)
        }
    return aggregated


def save_aggregated_results_to_csv(aggregated: dict, route_key: str, is_local: bool = True) -> str:
    """
    Сохраняет агрегированные результаты в CSV-файл.
    :param aggregated: Словарь с агрегированными метриками.
    :param route_key: Ключ роута.
    :param is_local: Флаг, указывающий на локальный запуск.
    """
    date_time = datetime.now().strftime("%Y%m%d_%H%M")
    mode = "local" if is_local else "api"
    output_csv = REPORTS_DIR / f"aggregated_{mode}_results_{date_time}_{route_key}.csv"
    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as file:
        fieldnames = ["metric", "min", "max", "mean", "p90"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for metric, values in aggregated.items():
            writer.writerow({"metric": metric, **values})

    print(f"[✔] Сохранено: {output_csv}")
    return str(output_csv)


def process_crux_results(crux_data: str, route_key: str,
                         device: str, gsheet_client,
                         worksheet_name: str):
    """
    Обрабатывает CrUX данные и отправляет их в Google Sheets.
    :param worksheet_name:
    :param crux_data:  с данными от API CrUX.
    :param route_key: Ключ роута.
    :param device: Тип устройства ("desktop" или "mobile").
    :param gsheet_client: Клиент для работы с Google Sheets.
    """
    # Парсим CrUX данные
    crux_metrics = parse_crux_results(crux_data)
    if not crux_metrics:
        print(f"[!] Нет данных для роута {route_key}.")
        return

    # Формируем строку для Google Sheets
    timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    row = {
        "timestamp": timestamp,
        "route_key": route_key,
        "device": device,
        **crux_metrics
    }

    # Отправляем данные в Google Sheets
    if gsheet_client:
        print(f"[DEBUG] Запись CrUX данных в Google Sheets для роута: {route_key}")
        gsheet_client.append_result(row)
        print(f"[✔] CrUX данные успешно загружены в Google Sheets {worksheet_name}")


def process_and_save_results(json_paths: List[str], route_key: str,
                             device_type: str,
                             gsheet_client, is_local: bool = True):
    """
    Обрабатывает список JSON-файлов: парсинг, агрегация, сохранение в CSV и запись в Google Sheets.
    :param json_paths: Список путей к JSON-файлам.
    :param route_key: Ключ роута.
    :param device_type: Тип устройства (desktop или mobile).
    :param gsheet_client: Клиент для работы с Google Sheets.
    :param is_local: Флаг, указывающий на локальный запуск.
    """

    temp_dir = TEMP_REPORTS_DIR
    # Парсинг JSON-файлов
    print(f"[DEBUG] Начало обработки JSON-файлов для роута: {route_key}")
    parsed_results = [parse_lighthouse_results(path) for path in json_paths]

    # Агрегация результатов
    print(f"[DEBUG] Агрегация результатов для роута: {route_key}")
    aggregated_results = aggregate_results(parsed_results)

    # Сохранение в CSV
    print(f"[DEBUG] Сохранение результатов в CSV для роута: {route_key}")
    csv_file_path = save_aggregated_results_to_csv(aggregated_results, route_key, is_local)
    # Очистка временных файлов
    if temp_dir and os.path.exists(csv_file_path):
        print(f"[DEBUG] Удаление временных результатов для роута: {route_key}")
        cleanup_temp_files(temp_dir)

    # Запись в Google Sheets
    if gsheet_client:
        environment = get_current_environment()
        worksheet_name = get_worksheet_name(environment, is_local)
        gsheet_client.worksheet_name = worksheet_name  # Устанавливаем имя листа

        contour = environment
        full_url = get_full_url(route_key)
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        row = build_row(timestamp, "ProjectName", full_url, route_key, device_type, contour, aggregated_results)

        print(f"[DEBUG] Запись результатов в Google Sheets для роута: {route_key}")
        gsheet_client.append_result(row)
        print("[✔] Данные успешно загружены в Google Sheets")


def build_row(timestamp: str, project: str,
        full_url: str, route_key: str,
        device_type: str, contour: str,
        aggregated: dict) -> dict:
    """
    Формирует строку для записи в Google Sheets.
    :param timestamp: Временная метка.
    :param project: Название проекта.
    :param full_url: Полный URL роута.
    :param route_key: Ключ роута.
    :param device_type: Тип устройства.
    :param contour: Контур (окружение).
    :param aggregated: Агрегированные метрики.
    :return: Список значений для строки.
    """
    flat = flatten_aggregated_metrics(aggregated)
    flat = flatten_aggregated_metrics(aggregated)
    return {
        "timestamp": timestamp,
        "project": project,
        "url": build_route_link(full_url, route_key),
        "device_type": device_type,
        "contour": contour,
        "performance_min": flat["performance_min"],
        "lcp_min": flat["lcp_min"],
        "fcp_min": flat["fcp_min"],
        "tbt_min": flat["tbt_min"],
        "cls_min": flat["cls_min"],
        "si_min": flat["si_min"],
        "tti_min": flat["tti_min"],  # Добавлено TTI
        "performance_max": flat["performance_max"],
        "lcp_max": flat["lcp_max"],
        "fcp_max": flat["fcp_max"],
        "tbt_max": flat["tbt_max"],
        "cls_max": flat["cls_max"],
        "si_max": flat["si_max"],
        "tti_max": flat["tti_max"],  # Добавлено TTI
        "performance_mean": flat["performance_mean"],
        "lcp_mean": flat["lcp_mean"],
        "fcp_mean": flat["fcp_mean"],
        "tbt_mean": flat["tbt_mean"],
        "cls_mean": flat["cls_mean"],
        "si_mean": flat["si_mean"],
        "tti_mean": flat["tti_mean"],  # Добавлено TTI
        "performance_p90": flat["performance_p90"],
        "lcp_p90": flat["lcp_p90"],
        "fcp_p90": flat["fcp_p90"],
        "tbt_p90": flat["tbt_p90"],
        "cls_p90": flat["cls_p90"],
        "si_p90": flat["si_p90"],
        "tti_p90": flat["tti_p90"],  # Добавлено TTI
    }


def flatten_aggregated_metrics(aggregated: dict) -> dict:
    """
    Преобразует вложенные метрики в плоский словарь.
    :param aggregated: Словарь с агрегированными метриками.
    :return: Плоский словарь.
    """
    flat = {}
    for metric, values in aggregated.items():
        for key, value in values.items():
            flat[f"{metric}_{key}"] = value
    return flat

def build_route_link(full_url: str, route_key: str) -> str:
    """
    Формирует гиперссылку для Google Sheets.
    :param full_url: Полный URL роута.
    :param route_key: Ключ роута.
    :return: Гиперссылка в формате Google Sheets.
    """
    return f'=HYPERLINK("{full_url}", "{route_key}")'


def ensure_sheet_exists(client, spreadsheet_id: str, sheet_name: str, template_name: str):
    """
    Проверяет существование листа в Google Sheets. Если лист отсутствует, создаёт его на основе шаблона.
    :param client: Экземпляр клиента Google Sheets.
    :param spreadsheet_id: ID таблицы Google Sheets.
    :param sheet_name: Имя листа, который нужно проверить или создать.
    :param template_name: Имя шаблона для создания нового листа.
    """
    existing_sheets = client.get_all_sheets(spreadsheet_id)
    if sheet_name not in existing_sheets:
        print(f"[INFO] Лист '{sheet_name}' отсутствует. Создаём на основе шаблона '{template_name}'.")
        client.duplicate_sheet(spreadsheet_id, template_name, sheet_name)
    else:
        print(f"[DEBUG] Лист '{sheet_name}' уже существует.")