# 📌 Google Lighthouse API (будет добавлен позже)
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Optional


def _retry_request(url: str, max_retries: int = 5, base_delay: float = 2.0) -> bytes:
    """
    Выполняет HTTP-запрос с retry и exponential backoff.

    При 429/5xx — ждёт base_delay * 2^attempt + jitter, повторяет.
    При 429 — парсит Retry-After header если есть.
    """
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            status = e.code
            is_retryable = status == 429 or status >= 500
            if not is_retryable or attempt == max_retries:
                print(f"[ERROR] HTTP {status} на попытке {attempt + 1}/{max_retries + 1}, retry исчерпаны")
                raise

            # Вычисляем задержку
            retry_after = e.headers.get("Retry-After") if status == 429 else None
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = base_delay * (2 ** attempt)
            else:
                delay = base_delay * (2 ** attempt)

            jitter = random.uniform(0, delay * 0.3)
            total_delay = delay + jitter
            print(f"[RETRY] HTTP {status}, попытка {attempt + 1}/{max_retries + 1}, ожидание {total_delay:.1f}с...")
            time.sleep(total_delay)

        except urllib.error.URLError as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[RETRY] URLError: {e.reason}, попытка {attempt + 1}/{max_retries + 1}, ожидание {delay:.1f}с...")
            time.sleep(delay)


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
        raw = _retry_request(full_url)
        result = json.loads(raw.decode())

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
