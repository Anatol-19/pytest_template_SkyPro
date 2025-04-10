import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List
from gspread.exceptions import APIError


class GoogleSheetsClient:
    """
    Клиент для взаимодействия с Google Таблицами через сервисный аккаунт.
    Позволяет добавлять строки с данными и управлять заголовками таблицы.

    Пример использования:
        client = GoogleSheetsClient(
            credentials_path="service_account.json",
            spreadsheet_id="your_spreadsheet_id_here",
            worksheet_name="Lighthouse Results"
        )

        client.append_result({
            "timestamp": "2025-04-07 15:00",
            "url": "https://example.com",
            "score": 92
        })
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str, worksheet_name: str):
        """
        Инициализация клиента и подключение к нужному листу таблицы.
        :param credentials_path: Путь к JSON-файлу с ключами сервисного аккаунта
        :param spreadsheet_id: ID таблицы Google Sheets
        :param worksheet_name: Название листа, с которым будет вестись работа
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = self._authorize()
        self.sheet = self._open_sheet()

    def _authorize(self):
        """Авторизация через сервисный аккаунт"""
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        return gspread.authorize(credentials)

    def _open_sheet(self):
        """Открытие таблицы и листа. Создание листа, если не найден."""
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=100, cols=20)
        return worksheet

    def append_result(self, data: Dict[str, any]):
        """
        Добавляет результат в конец таблицы. Если таблица пуста — создает заголовки.

        :param data: Словарь, где ключ — название колонки, значение — значение ячейки
        """
        headers = self._get_or_create_headers(data)
        row = [data.get(h, "") for h in headers]
        self.sheet.append_row(row, value_input_option="USER_ENTERED")

    def _get_or_create_headers(self, data: Dict[str, any]) -> List[str]:
        """
        Проверяет, есть ли заголовки в таблице. Если нет — создает их.
        Если появились новые ключи в data — добавляет их в заголовки.

        :param data: Словарь с текущими данными
        :return: Список заголовков в нужном порядке
        """
        try:
            current_headers = self.sheet.row_values(1)
        except APIError:
            current_headers = []

        # Если таблица пустая — создаем заголовки
        if not current_headers:
            headers = list(data.keys())
            self.sheet.insert_row(headers, 1)
            return headers

        # Добавим недостающие заголовки (новые ключи)
        missing = [k for k in data.keys() if k not in current_headers]
        if missing:
            current_headers += missing
            self.sheet.update('1:1', [current_headers])

        return current_headers
