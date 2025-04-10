"""
Модуль для выполнения тестов скорости с использованием Lighthouse.
"""
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from services.lighthouse.api_runner import run_lighthouse_api
from services.lighthouse.processor_lighthouse import process_lighthouse_batch

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.google.google_sheets_client import GoogleSheetsClient
from services.lighthouse.cli_runner import run_local_lighthouse
from services.lighthouse.config_lighthouse import get_base_url, load_routes_config, get_full_url, \
    get_current_environment, get_worksheet_name, REPORTS_DIR, TEMP_REPORTS_DIR, ensure_directories_exist

# Загружаем .env из папки lighthouse
dotenv_path = os.path.join(os.path.dirname(__file__), 'config_lighthouse.env')
load_dotenv(dotenv_path)


class SpeedtestService:
    """
        Класс для выполнения тестов скорости и обработки результатов.
        Отвечает только за orchestration.
        """
    iteration_counter = 0


    def __init__(self, reports_dir=REPORTS_DIR, temp_reports_dir=TEMP_REPORTS_DIR):
        """Инициализирует объект SpeedtestService."""
        SpeedtestService.iteration_counter += 1
        self.iteration = SpeedtestService.iteration_counter

        # Настройка путей для отчетов
        self.base_reports_dir = reports_dir
        self.temp_reports_dir = temp_reports_dir
        # Создаем директории, если они не существуют
        ensure_directories_exist()

        self.config = load_routes_config()
        self.date = datetime.now().strftime("%d-%m-%y")
        self.dateTime = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        self.environment = get_current_environment()


    def _initialize_google_client(self, is_local: bool) -> GoogleSheetsClient:
        """
        Инициализирует и возвращает экземпляр GoogleSheetsClient.
        :param is_local: Флаг, указывающий на локальный запуск.
        :return: Экземпляр GoogleSheetsClient.
        """
        credentials_path = os.path.join(os.path.dirname(__file__), os.getenv("GS_CREDS"))
        spreadsheet_id = os.getenv("GS_SHEET_ID")
        worksheet_name = get_worksheet_name(self.environment, is_local)

        if not credentials_path or not spreadsheet_id:
            raise RuntimeError("Не установлены переменные окружения для Google Sheets")

        return GoogleSheetsClient(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name
        )


    def prepare_routes(self, route_keys: list | str) -> list:
        """
        Формирует список кортежей (ключ, полный URL) для указанных ключей роутов.
        :param route_keys: Список ключей роутов из routes.ini.
         :return: Список кортежей (ключ, полный URL).
        """

        print(f"[DEBUG]: route_keys передан как: {route_keys} (тип: {type(route_keys)})")  # Отладка

        if isinstance(route_keys, str):
            route_keys = [route_keys]  # Преобразуем строку в список

        routes = []  # Локальная переменная для хранения кортежей
        for route_key in route_keys:
            try:
                full_url = get_full_url(route_key.strip())  # Убираем лишние пробелы

                print(f"[DEBUG]: route_key: {route_key}, full_url: {full_url}")  # Отладка

                routes.append((route_key, full_url))  # Связываем ключ с URL
            except KeyError:
                print(f"Роут с ключом '{route_key}' не найден в конфигурации.")
        return routes


    def run_local_tests(self, route_keys: list, device: str, iteration_count: int):
        """
        Выполняет тесты с использованием локального Lighthouse CLI.
        - вызывает run_local_lighthouse → сохраняет temp JSON-файлы
        - собирает их в список
        - вызывает processor_lighthouse.process_lighthouse_batch(json_paths=..., ...)
        :param route_keys: Список ключей роутов из routes.ini.
        :param device: Тип устройства (desktop или mobile).
        :param iteration_count: Количество итераций для каждой страницы.
        """
        # Инициализация GoogleSheetsClient
        google_client = self._initialize_google_client(True) # Локальный запуск

        routes = self.prepare_routes(route_keys)  # Получаем список кортежей (ключ, URL)
        for route_key, route_url in routes:
            print(f"[DEBUG]: Перед вызовом run_local_lighthouse: route_key={route_key}, route_url={route_url}")  # Отладка
            temp_dir = os.path.join(self.temp_reports_dir, f"{self.date}_local_{route_key}")
            os.makedirs(temp_dir, exist_ok=True)

            json_paths = run_local_lighthouse(route_key, route_url, iteration_count, device)

            process_lighthouse_batch(json_paths, route_key, device, google_client, is_local=True)


    def run_api_tests(self, route_keys: list, device: str):
        """
        Выполняет тесты с использованием Google Lighthouse API.
        - вызывает run_lighthouse_api
        - сохраняет 1 JSON
        - вызывает processor_lighthouse.process_lighthouse_batch(json_paths=[json_path], ...)
        :param routes: Список ключей роутов из routes.ini.
        :param device: Тип устройства (desktop или mobile).
        """
        # Инициализация GoogleSheetsClient
        google_client = self._initialize_google_client(False) # Удалённый запуск

        routes = self.prepare_routes(route_keys)  # Преобразуем ключи в список URL
        for route_key, route_url in routes:
            print(f"[DEBUG]: Запуск API Lighthouse для: {route_key} ({route_url})")
            json_result = run_lighthouse_api(route_url, strategy=device)

            json_path = self._save_api_result(json_result, route_key)

            process_lighthouse_batch([json_path], route_key, device, google_client, is_local=False)


    def _save_api_result(self, json_result: dict, route_key: str) -> str:
        """
        Сохраняет результат API в файл и возвращает путь.
        """
        temp_dir = os.path.join(self.temp_reports_dir, route_key)
        os.makedirs(temp_dir, exist_ok=True)
        json_path = os.path.join(temp_dir, "api_result.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        return json_path


"""Пример использования:"""
if __name__ == "__main__":
    base_url = get_base_url()  # Получаем базовый URL для текущего окружения
    iteration_count = 2  # Количество итераций можно изменить здесь
    device = "desktop"  # Тип устройства

    service = SpeedtestService()
    # service.run_local_tests(["home"], device, iteration_count)
    service.run_api_tests(["home"], device)