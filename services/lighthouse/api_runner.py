# 📌 Google Lighthouse API (будет добавлен позже)
import json
import os
import urllib.parse
import urllib.request
from typing import List, Optional

def run_lighthouse_api(
    url: str,
    strategy: str = "mobile",
    categories: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    save_path: Optional[str] = None
) -> dict:
    """
    Выполняет запрос к Google PageSpeed Insights API и сохраняет JSON-результат.

    :param url: URL страницы для анализа
    :param strategy: Тип устройства ("mobile" или "desktop")
    :param categories: Список категорий (например: ["performance", "accessibility"])
    :param api_key: Ключ API Google (опционально)
    :param save_path: Путь для сохранения JSON-отчета
    :return: dict — результат анализа Lighthouse
    """

    base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy
    }

    if categories:
        params["category"] = categories

    if api_key:
        params["key"] = api_key

    encoded_params = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{base_url}?{encoded_params}"

    with urllib.request.urlopen(full_url) as response:
        result = json.loads(response.read().decode())

    # Сохраняем результат в файл (если указан путь)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result