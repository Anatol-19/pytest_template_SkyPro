import gspread
import numpy as np
from typing import Dict, List, Optional, Any
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    """
    Клиент для взаимодействия с Google Sheets:
    - Поддерживает создание листов
    - Добавление заголовков
    - Построчную и пакетную запись
    - Автоматическое добавление новых колонок
    - Поддержка формул в ячейках
    """

    def __init__(self,
                 credentials_path: str,
                 spreadsheet_id: str,
                 worksheet_name: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = self._authorize()
        self.sheet = self._open_sheet()
        self._batch_rows = []  # Для накопления строк перед массовой отправкой

    def _authorize(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes
        )
        return gspread.authorize(credentials)

    def _open_sheet(self):
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            try:
                worksheet = spreadsheet.worksheet(self.worksheet_name)
            except WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=100, cols=30)
                print(f"[INFO] Создан новый лист: {self.worksheet_name}")
            return worksheet
        except Exception as e:
            print(f"[ERROR] Ошибка при открытии таблицы: {e}")
            raise

    def append_result(self, data: Dict[str, Any], raw_formula_fields: Optional[List[str]] = None):
        headers = self._get_or_create_headers(data)
        processed_data = self._normalize_data(data)

        row = []
        for h in headers:
            val = processed_data.get(h, "")
            if raw_formula_fields and h in raw_formula_fields:
                row.append(val)  # не экранируем формулу
            else:
                row.append(val)

        self._batch_rows.append(row)

    def _get_or_create_headers(self, data: Dict[str, Any]) -> List[str]:
        try:
            current_headers = self.sheet.row_values(1)
        except APIError:
            current_headers = []

        if not current_headers:
            headers = list(data.keys())
            self.sheet.insert_row(headers, 1)
            return headers

        missing = [k for k in data.keys() if k not in current_headers]
        if missing:
            current_headers += missing
            self.sheet.update('1:1', [current_headers])

        return current_headers

    def flush(self):
        if not self._batch_rows:
            print("[DEBUG] Нет строк для отправки.")
            return

        try:
            print(f"[INFO] Отправка {len(self._batch_rows)} строк в Google Sheets...")
            self.sheet.append_rows(self._batch_rows, value_input_option="USER_ENTERED")
            self._batch_rows.clear()
        except Exception as e:
            print(f"[ERROR] Не удалось записать данные в Google Sheets: {e}")
            raise

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, val in data.items():
            if isinstance(val, (np.int32, np.int64)):
                result[key] = int(val)
            elif isinstance(val, (np.float32, np.float64)):
                result[key] = float(val)
            else:
                result[key] = val
        return result

    @staticmethod
    def prepare_link(anchor: str, url: str) -> str:
        """Формирует строку для вставки гиперссылки в таблицу."""
        return f'=HYPERLINK("{url}", "{anchor}")'
