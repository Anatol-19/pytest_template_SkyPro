import json
import os
import csv
import numpy as np


def parse_lighthouse_results(json_file: str) -> dict:
    """Парсит JSON-отчет Lighthouse и извлекает ключевые метрики."""
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    metrics = {
        "performance": data["categories"]["performance"]["score"] * 100,
        "lcp": data["audits"]["largest-contentful-paint"]["numericValue"],
        "fcp": data["audits"]["first-contentful-paint"]["numericValue"],
        "tbt": data["audits"]["total-blocking-time"]["numericValue"],
        "cls": data["audits"]["cumulative-layout-shift"]["numericValue"],
        "si": data["audits"]["speed-index"]["numericValue"]
    }
    return metrics


def aggregate_results(results: list) -> dict:
    """Агрегирует результаты: min, max, среднее и 90-й процентиль."""
    aggregated = {}
    for metric in results[0].keys():
        values = [res[metric] for res in results]
        aggregated[metric] = {
            "min": np.min(values),
            "max": np.max(values),
            "mean": np.mean(values),
            "p90": np.percentile(values, 90)
        }
    return aggregated


def save_aggregated_results_to_csv(aggregated: dict, output_csv: str):
    """Сохраняет агрегированные результаты в CSV-файл."""
    file_exists = os.path.isfile(output_csv)

    with open(output_csv, "a", newline="", encoding="utf-8") as file:
        fieldnames = ["metric", "min", "max", "mean", "p90"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for metric, values in aggregated.items():
            writer.writerow({"metric": metric, **values})
