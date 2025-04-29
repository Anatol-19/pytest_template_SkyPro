# 📌 Google Lighthouse API (будет добавлен позже)
import json
import os
import urllib.parse
import urllib.request
from typing import List, Optional

def run_api_lighthouse(
    url: str,
    strategy: str = "mobile",
    categories: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    save_path: Optional[str] = None,
    mode: str = "lab"
) -> dict:
    """
    Выполняет запрос к Google PageSpeed Insights API и сохраняет JSON-результат.
    """

    base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    if api_key is None:
        api_key = os.getenv("API_KEY")

    if not api_key:
        raise ValueError("❌ API Key не указан. Установите переменную окружения API_KEY или передайте явно.")

    params = {
        "url": url,
        "strategy": strategy,
        "key": api_key
    }

    if categories:
        params["category"] = categories

    encoded_params = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{base_url}?{encoded_params}"

    try:
        with urllib.request.urlopen(full_url) as response:
            result = json.loads(response.read().decode())

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        if mode == "field":
            return result.get("loadingExperience", {})
        elif mode == "lab":
            return result.get("lighthouseResult", {})
        else:
            raise ValueError(f"Неверный режим: {mode}")

    except Exception as e:
        print(f"[ERROR] Ошибка при выполнении запроса к API: {e}")
        return {}
