import gspread
import numpy as np
from typing import Dict, List, Optional, Any, Literal
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    """
    Клиент для взаимодействия с Google Sheets:
    - Авторизация через сервисный аккаунт
    - Создание листов (в том числе из шаблонов)
    - Автообновление заголовков
    - Поддержка пакетной записи
    - Формулы и гиперссылки
    """

    def __init__(
        self,
        credentials_path: str,
        spreadsheet_id: str,
        worksheet_name: str
    ):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = self._authorize()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.sheet = self._open_or_create_sheet(worksheet_name)
        self._batch_rows: List[List[Any]] = []

    def _authorize(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes
        )
        return gspread.authorize(credentials)

    def _open_or_create_sheet(self, sheet_name: str):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except WorksheetNotFound:
            print(f"[INFO] Лист '{sheet_name}' не найден. Создаём новый.")
            return self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=30)

    def append_result(self, data: Dict[str, Any], raw_formula_fields: Optional[List[str]] = None):
        """
        Добавляет строку (в память) для последующей batch-записи.
        Автоматически дополняет заголовки, если появляются новые ключи.
        """
        headers = self._get_or_create_headers(data)
        processed_data = self._normalize_data(data)

        row = []
        for h in headers:
            val = processed_data.get(h, "")
            row.append(val)

        self._batch_rows.append(row)

    def flush(self):
        """
        Отправляет накопленные строки в Google Sheets одним вызовом.
        """
        if not self._batch_rows:
            print("[DEBUG] Нет строк для отправки.")
            return

        try:
            print(f"[INFO] Запись {len(self._batch_rows)} строк в таблицу '{self.worksheet_name}'...")
            self.sheet.append_rows(self._batch_rows, value_input_option="USER_ENTERED")
            self._batch_rows.clear()
        except Exception as e:
            print(f"[ERROR] Не удалось выполнить batch-запись: {e}")
            raise

    def append_result_to_sheet(self, sheet_name: str, row: Dict[str, Any]):
        """
        Добавляет строку напрямую в указанный лист.
        """
        try:
            target_sheet = self.spreadsheet.worksheet(sheet_name)
            values = list(row.values())
            target_sheet.append_row(values, value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении строки в '{sheet_name}': {e}")
            raise


    def ensure_sheet_exists(self, sheet_name: str, source: Literal["cli", "api", "crux"]):
        """
        Проверяет наличие листа. Если отсутствует — клонирует из шаблона по типу источника.
        :param sheet_name: Имя создаваемого листа.
        :param source: Тип источника — определяет, из какого шаблона клонировать ('cli', 'api', 'crux').
        """
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if sheet_name not in sheet_titles:
                from services.lighthouse.configs.config_lighthouse import TEMPLATE_SHEETS  # 👈 оттуда берём шаблон
                template_name = TEMPLATE_SHEETS.get(source.lower())
                if not template_name:
                    raise ValueError(f"Неизвестный шаблон для source={source}")
                print(f"[INFO] Создаём лист '{sheet_name}' из шаблона '{template_name}'...")
                template_sheet = spreadsheet.worksheet(template_name)
                spreadsheet.duplicate_sheet(template_sheet.id, new_sheet_name=sheet_name)
            else:
                print(f"[DEBUG] Лист '{sheet_name}' уже существует.")
        except Exception as e:
            print(f"[ERROR] Ошибка при создании листа из шаблона: {e}")
            raise

    def _get_or_create_headers(self, data: Dict[str, Any]) -> List[str]:
        """
        Получает текущие заголовки из таблицы. Если заголовки отсутствуют — создаёт их на основе переданных данных.
        Также добавляет новые столбцы, если в data появились новые ключи.

        :param data: Словарь, где ключ — имя столбца, значение — значение ячейки.
        :return: Обновлённый список заголовков в порядке, в котором они будут использоваться в таблице.
        """
        try:
            current_headers = self.sheet.row_values(1)
        except APIError:
            current_headers = []

        if not current_headers:
            # Первая запись — заголовки по ключам из data
            headers = list(data.keys())
            self.sheet.insert_row(headers, index=1)
            return headers

        # Проверка на новые поля, которых ещё нет в таблице
        missing_headers = [key for key in data.keys() if key not in current_headers]
        if missing_headers:
            updated_headers = current_headers + missing_headers
            self.sheet.update('1:1', [updated_headers])
            return updated_headers

        return current_headers

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует типы данных в поддерживаемые Google Sheets.
        """
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
        """
        Генерирует формулу HYPERLINK для вставки в ячейку.
        """
        return f'=HYPERLINK("{url}"; "{anchor}")'
