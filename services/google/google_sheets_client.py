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
        self._headers: Optional[List[str]] = None  # Сохраняем порядок заголовков

    def _authorize(self):
        """
        Авторизация через сервисный аккаунт.
        """
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes
        )
        return gspread.authorize(credentials)

    def _open_or_create_sheet(self, sheet_name: str):
        """
        Пытается открыть существующий лист, иначе создаёт новый.
        """
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except WorksheetNotFound:
            print(f"[INFO] Лист '{sheet_name}' не найден. Создаём новый.")
            return self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=30)

    def append_result(self, data: Dict[str, Any], raw_formula_fields: Optional[List[str]] = None):
        """
        Добавляет строку (в память) для последующей batch-записи.
        Автоматически дополняет заголовки, если появляются новые ключи.

        :param data: Словарь с данными для строки.
        :param raw_formula_fields: Не используется в текущей реализации, можно использовать для вставки формул.
        """
        headers = self._get_or_create_headers(data)
        self._headers = headers  # Зафиксировать порядок заголовков
        processed_data = self._normalize_data(data)

        # Формируем строку в соответствии с заголовками
        row = [processed_data.get(h, "") for h in headers]
        self._batch_rows.append(row)

    def flush(self):
        """
        Отправляет накопленные строки в Google Sheets одним вызовом.
        Начинает со строки A4 или следующей пустой после уже записанных строк.
        """
        if not self._batch_rows:
            print("[DEBUG] Нет строк для отправки.")
            return

        try:
            print(f"[INFO] Запись {len(self._batch_rows)} строк в таблицу '{self.worksheet_name}'...")

            existing_data = self.sheet.get_all_values()
            start_row = max(4, len(existing_data) + 1)  # Не раньше A4
            max_len = len(self._headers or [])

            padded_rows = [r + [""] * (max_len - len(r)) for r in self._batch_rows]
            range_start = f"A{start_row}"

            self.sheet.update(range_start, padded_rows, value_input_option="USER_ENTERED")
            self._batch_rows.clear()

            print(f"[INFO] Успешно записано с {range_start} ({len(padded_rows)} строк).")
        except Exception as e:
            print(f"[ERROR] Не удалось выполнить batch-запись: {e}")
            raise

    def append_result_to_sheet(self, sheet_name: str, row: Dict[str, Any]):
        """
        Добавляет строку напрямую в указанный лист.

        :param sheet_name: Название листа.
        :param row: Данные строки.
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
                from services.lighthouse.configs.config_lighthouse import TEMPLATE_SHEETS
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
            headers = list(data.keys())
            self.sheet.insert_row(headers, index=1)
            return headers

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

        :param anchor: Текст ссылки.
        :param url: URL-адрес.
        :return: Строка с формулой Google Sheets для гиперссылки.
        """
        return f'=HYPERLINK("{url}"; "{anchor}")'