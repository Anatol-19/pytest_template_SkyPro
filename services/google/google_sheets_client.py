import json
import os
import random
import time
import threading

import gspread
import numpy as np
from typing import Dict, List, Optional, Any, Literal
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials

FAILED_FLUSH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Reports", "reports_lighthouse",
)

# Межпроцессный rate limiter для Google Sheets API через lock-файл
_SHEETS_LOCK_DIR = os.path.join(FAILED_FLUSH_DIR, ".sheets_locks")
_SHEETS_MIN_INTERVAL = 1.5  # минимум секунд между Sheets API вызовами


def _sheets_rate_limit():
    """Простой межпроцессный rate limiter через timestamp файл."""
    os.makedirs(_SHEETS_LOCK_DIR, exist_ok=True)
    ts_file = os.path.join(_SHEETS_LOCK_DIR, "last_call.txt")
    for _ in range(30):  # макс 45 секунд ожидания
        try:
            now = time.time()
            if os.path.exists(ts_file):
                try:
                    with open(ts_file, "r") as f:
                        last = float(f.read().strip())
                    elapsed = now - last
                    if elapsed < _SHEETS_MIN_INTERVAL:
                        time.sleep(_SHEETS_MIN_INTERVAL - elapsed + random.uniform(0.1, 0.5))
                except (ValueError, OSError):
                    pass
            with open(ts_file, "w") as f:
                f.write(str(time.time()))
            return
        except OSError:
            time.sleep(random.uniform(0.3, 0.8))


def _retry_sheets_call(func, max_retries=5, base_delay=2.0):
    """
    Обёртка для вызовов Google Sheets API с retry и exponential backoff.
    Ретраит при APIError (429, 5xx) и общих сетевых ошибках.
    Включает межпроцессный rate limiting.
    """
    for attempt in range(max_retries + 1):
        try:
            _sheets_rate_limit()
            return func()
        except APIError as e:
            status = e.response.status_code if hasattr(e, 'response') and e.response else 500
            is_retryable = status == 429 or status >= 500
            if not is_retryable or attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[RETRY] Sheets API {status}, попытка {attempt + 1}/{max_retries + 1}, ожидание {delay:.1f}с...")
            time.sleep(delay)
        except Exception:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[RETRY] Sheets ошибка, попытка {attempt + 1}/{max_retries + 1}, ожидание {delay:.1f}с...")
            time.sleep(delay)


class GoogleSheetsClient:
    """Client helper for Google Sheets."""

    def __init__(self, credentials_path: str, spreadsheet_id: str, worksheet_name: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = self._authorize()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.sheet = self._open_or_create_sheet(worksheet_name)
        self._batch_rows: List[List[Any]] = []
        self._headers: Optional[List[str]] = None
        self._headers_cached: bool = False
        self._next_row: Optional[int] = None  # кэш позиции для append

    def _authorize(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        return gspread.authorize(credentials)

    def _open_or_create_sheet(self, sheet_name: str):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except WorksheetNotFound:
            print(f"[INFO] Лист '{sheet_name}' не найден. Создаём новый.")
            return self.spreadsheet.add_worksheet(title=sheet_name, rows=200, cols=60)

    def append_result(self, data: Dict[str, Any], raw_formula_fields: Optional[List[str]] = None):
        headers = self._get_or_create_headers(data)
        self._headers = headers
        processed = self._normalize_data(data)
        row = [processed.get(h, "") for h in headers]
        self._batch_rows.append(row)

    def flush(self):
        if not self._batch_rows:
            print("[DEBUG] Нет строк для отправки.")
            return

        rows_to_write = list(self._batch_rows)

        def _do_flush():
            print(f"[INFO] Запись {len(rows_to_write)} строк в таблицу '{self.worksheet_name}'...")
            # Определяем start_row: используем кэш или делаем один лёгкий запрос
            if self._next_row is not None:
                start_row = self._next_row
            else:
                # Один вызов вместо get_all_values() — считаем только кол-во строк
                try:
                    col_a = self.sheet.col_values(1)
                    start_row = max(4, len(col_a) + 1)
                except Exception:
                    start_row = 4
            max_len = len(self._headers or [])
            padded = [r + [""] * (max_len - len(r)) for r in rows_to_write]
            range_start = f"A{start_row}"
            self.sheet.update(range_start, padded, value_input_option="USER_ENTERED")
            # Обновляем кэш позиции
            self._next_row = start_row + len(padded)
            print(f"[INFO] Успешно записано с {range_start} ({len(padded)} строк).")

        try:
            _retry_sheets_call(_do_flush)
            self._batch_rows.clear()
        except Exception as e:
            print(f"[ERROR] Не удалось выполнить batch-запись после всех retry: {e}")
            self._save_failed_flush(rows_to_write)
            self._batch_rows.clear()
            raise

    def _save_failed_flush(self, rows: List[List[Any]]):
        """Сохраняет неотправленные строки в JSON-файл как fallback."""
        os.makedirs(FAILED_FLUSH_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(FAILED_FLUSH_DIR, f"failed_flush_{timestamp}.json")
        payload = {
            "worksheet_name": self.worksheet_name,
            "spreadsheet_id": self.spreadsheet_id,
            "headers": self._headers,
            "rows": rows,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
            print(f"[FALLBACK] Данные сохранены в {path}")
        except Exception as ex:
            print(f"[ERROR] Не удалось сохранить fallback JSON: {ex}")

    def retry_failed_flushes(self):
        """Повторно отправляет данные из ранее сохранённых fallback-файлов."""
        if not os.path.isdir(FAILED_FLUSH_DIR):
            print("[INFO] Директория fallback не найдена, нечего повторять.")
            return

        pattern = "failed_flush_"
        files = [f for f in os.listdir(FAILED_FLUSH_DIR) if f.startswith(pattern) and f.endswith(".json")]
        if not files:
            print("[INFO] Нет failed flush файлов для повторной отправки.")
            return

        for filename in sorted(files):
            filepath = os.path.join(FAILED_FLUSH_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                rows = payload.get("rows", [])
                headers = payload.get("headers", [])
                ws_name = payload.get("worksheet_name", self.worksheet_name)

                if not rows:
                    os.remove(filepath)
                    continue

                sheet = self.spreadsheet.worksheet(ws_name)

                def _do_retry_flush():
                    existing = sheet.get_all_values()
                    start_row = max(4, len(existing) + 1)
                    max_len = len(headers) if headers else max((len(r) for r in rows), default=0)
                    padded = [r + [""] * (max_len - len(r)) for r in rows]
                    range_start = f"A{start_row}"
                    sheet.update(range_start, padded, value_input_option="USER_ENTERED")
                    print(f"[INFO] Retry flush: записано {len(padded)} строк в '{ws_name}' с {range_start}")

                _retry_sheets_call(_do_retry_flush)
                os.remove(filepath)
                print(f"[INFO] Файл {filename} обработан и удалён.")
            except Exception as e:
                print(f"[ERROR] Не удалось повторить flush из {filename}: {e}")

    def append_result_to_sheet(self, sheet_name: str, row: Dict[str, Any]):
        try:
            target_sheet = self.spreadsheet.worksheet(sheet_name)
            values = list(row.values())
            target_sheet.append_row(values, value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении строки в '{sheet_name}': {e}")
            raise

    DEFAULT_HEADERS = {
        "cli": [
            "date", "project", "environment", "source", "sprint", "run_id", "tag", "type", "page", "device", "iterations",
            "P", "LCP", "INP", "CLS", "LCP_p90", "INP_p90", "CLS_p90",
            "TBT", "FCP", "SI", "TTI", "TTFB"
        ],
        "api": [
            "date", "project", "environment", "source", "sprint", "run_id", "tag", "type", "page", "device", "iterations",
            "P", "LCP", "INP", "CLS", "LCP_p90", "INP_p90", "CLS_p90",
            "TBT", "FCP", "SI", "TTI", "TTFB"
        ],
        "crux": [
            "date", "project", "environment", "source", "sprint", "run_id", "tag", "type", "page", "device", "iterations",
            "LCP", "FCP", "INP", "CLS",
            "LCP_good_pct", "FCP_good_pct", "INP_good_pct", "CLS_good_pct",
            "TTFB"
        ],
    }

    def ensure_sheet_exists(self, sheet_name: str, source: Literal["cli", "api", "crux"]):
        def _do_ensure():
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if sheet_name not in sheet_titles:
                from services.lighthouse.configs.config_lighthouse import TEMPLATE_SHEETS
                template_name = TEMPLATE_SHEETS.get(source.lower())
                if template_name and template_name in sheet_titles:
                    print(f"[INFO] Создаём лист '{sheet_name}' из шаблона '{template_name}'...")
                    template_sheet = spreadsheet.worksheet(template_name)
                    spreadsheet.duplicate_sheet(template_sheet.id, new_sheet_name=sheet_name)
                else:
                    print(f"[INFO] Создаём лист '{sheet_name}' с заголовками по умолчанию...")
                    new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows=200, cols=60)
                    headers = self.DEFAULT_HEADERS.get(source.lower(), [])
                    if headers:
                        new_sheet.update('1:1', [headers])
                self.sheet = spreadsheet.worksheet(sheet_name)
            else:
                self.sheet = spreadsheet.worksheet(sheet_name)

        try:
            _retry_sheets_call(_do_ensure)
        except Exception as e:
            print(f"[ERROR] Ошибка при создании листа: {e}")
            raise

    def _get_or_create_headers(self, data: Dict[str, Any]) -> List[str]:
        # Возвращаем кэш если headers уже загружены и все ключи присутствуют
        if self._headers_cached and self._headers:
            missing = [k for k in data.keys() if k not in self._headers]
            if not missing:
                return self._headers

        def _do_headers():
            try:
                current_headers = self.sheet.row_values(1)
            except APIError:
                current_headers = []
            if not current_headers:
                headers = list(data.keys())
                self.sheet.insert_row(headers, index=1)
                return headers
            missing = [k for k in data.keys() if k not in current_headers]
            if missing:
                updated = current_headers + missing
                self.sheet.update('1:1', [updated])
                return updated
            return current_headers

        result = _retry_sheets_call(_do_headers)
        self._headers_cached = True
        return result

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for k, v in data.items():
            if isinstance(v, (np.integer, np.int32, np.int64)):
                normalized[k] = int(v)
            elif isinstance(v, (np.floating, np.float32, np.float64)):
                normalized[k] = float(v)
            else:
                normalized[k] = v
        return normalized

    @staticmethod
    def prepare_link(anchor: str, url: str) -> str:
        return f'=HYPERLINK("{url}"; "{anchor}")'


    @classmethod
    def read_dashboard_sprint_context(cls, credentials_path: str, spreadsheet_id: str, project: str) -> Dict[str, Any]:
        client = cls(credentials_path=credentials_path, spreadsheet_id=spreadsheet_id, worksheet_name=f"Dashboard [{project}]")
        sheet = client.sheet
        current_sprint = str(sheet.acell("E5").value or "").strip()
        previous_increment = str(sheet.acell("E6").value or "").strip()
        rollout = {
            "DEV": sheet.acell("D9").value == "TRUE",
            "TEST": sheet.acell("E9").value == "TRUE",
            "STAGE": sheet.acell("F9").value == "TRUE",
            "PROD": sheet.acell("G9").value == "TRUE",
        }
        has_any_rollout = any(rollout.values())
        return {
            "current_sprint": current_sprint,
            "previous_increment": previous_increment,
            "rollout": rollout,
            "has_any_rollout": has_any_rollout,
            "active_sprint": current_sprint or previous_increment,
        }
