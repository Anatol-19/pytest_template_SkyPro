"""
Модуль для выполнения тестов скорости с использованием Lighthouse.
"""
import argparse
from pathlib import Path
import json
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from requests import RequestException

from services.lighthouse.api_runner import run_lighthouse_api
from services.lighthouse.processor_lighthouse import process_and_save_results, process_crux_results

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.google.google_sheets_client import GoogleSheetsClient
from services.lighthouse.cli_runner import run_local_lighthouse
from services.lighthouse.configs.config_lighthouse import get_base_url, load_routes_config, get_full_url, \
    get_current_environment, get_worksheet_name, REPORTS_DIR, TEMP_REPORTS_DIR, ensure_directories_exist, \
    get_temp_dir_for_route, get_google_creds_path

# Загружаем .env из папки lighthouse/configs
dotenv_path = os.path.join(os.path.dirname(__file__), 'configs', 'config_lighthouse.env')
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
        self.worksheet_name : str


    def _initialize_google_client(self, is_local: bool) -> GoogleSheetsClient:
        """
        Инициализирует и возвращает экземпляр GoogleSheetsClient.
        :param is_local: Флаг, указывающий на локальный запуск.
        :return: Экземпляр GoogleSheetsClient.
        """
        credentials_env = os.getenv("GS_CREDS")
        if not credentials_env:
            raise ValueError(
                "Переменная окружения 'GS_CREDS' не задана. Укажите путь к файлу с учетными данными в .env.")

        credentials_path = get_google_creds_path()
        # credentials_path = Path(__file__).parent / credentials_env
        spreadsheet_id = os.getenv("GS_SHEET_ID")
        self.worksheet_name = get_worksheet_name(self.environment, is_local)

        if not spreadsheet_id:
            raise RuntimeError("Не установлены переменные окружения для Google Sheets")

        try:
            return GoogleSheetsClient(
                credentials_path=str(credentials_path),
                spreadsheet_id=spreadsheet_id,
                worksheet_name=self.worksheet_name
            )
        except RefreshError as e:
            print(f"Ошибка аутентификации: {e}")
            # Здесь можно добавить логику для повторной попытки или уведомления администратора
            raise  # Повторно выбрасываем исключение, чтобы остановить выполнение


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


    @staticmethod
    def load_config(mode: str) -> dict:
        """
        Загружает конфигурацию из файла в зависимости от режима.
        :param mode: Режим запуска (desktop или mobile).
        :return: Словарь с конфигурацией.
        """
        config_file = f"config_{mode}.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Конфигурационный файл {config_file} не найден.")
        with open(config_file, "r", encoding="utf-8") as file:
            return json.load(file)


    def run_local_tests(self, route_keys: list, device_type: str, n_iteration: int):
        """
        Выполняет тесты с использованием локального Lighthouse CLI.
        - вызывает run_local_lighthouse → сохраняет temp JSON-файлы
        - собирает их в список
        - вызывает processor_lighthouse.process_lighthouse_batch(json_paths=..., ...)
        :param route_keys: Список ключей роутов из routes.ini.
        :param device_type: Тип устройства (desktop или mobile).
        :param n_iteration: Количество итераций для каждой страницы.
        """
        # Инициализация GoogleSheetsClient
        google_client = self._initialize_google_client(True) # Локальный запуск

        routes = self.prepare_routes(route_keys)  # Получаем список кортежей (ключ, URL)
        for route_key, route_url in routes:
            print(f"[DEBUG]: Перед вызовом run_local_lighthouse: route_key={route_key}, route_url={route_url}")  # Отладка

            # Проверяем доступность сайта
            if not self._check_site_availability(route_url):
                print(f"[ERROR] Сайт {route_url} недоступен. Пропускаем тест для роута {route_key}.")
                continue

            # temp_dir = self._keep_dir(f"{self.date}_{route_key}_{device_type}_L")
            temp_dir = get_temp_dir_for_route(route_key, device_type, True)

            json_paths = run_local_lighthouse(route_key, route_url, n_iteration, device_type)

            process_and_save_results(json_paths, route_key, device_type, google_client, is_local=True)


    def run_api_aggregated_tests(self, route_keys: list, device_type: str, n_iteration: int = 3):
        """
        Выполняет агрегируемый запуск по API для получения Core Web Vitals и ключевых метрик Lighthouse.
        :param route_keys: Список ключей роутов.
        :param device_type: Тип устройства (desktop или mobile).
        :param n_iteration: Количество итераций для каждой страницы.
        """
        google_client = self._initialize_google_client(False)  # Удалённый запуск
        routes = self.prepare_routes(route_keys) # Преобразуем ключи в список URL

        for route_key, route_url in routes:
            print(f"[DEBUG]: Запуск агрегируемого API Lighthouse для: {route_key} ({route_url})")

            # Создаём временную папку для роута
            temp_dir = get_temp_dir_for_route(route_key, device_type, True)
            json_paths = []  # Список для хранения путей к JSON-файлам

            for _ in range(n_iteration):
                json_result = run_lighthouse_api(
                    url=route_url,
                    strategy=device_type,
                    categories=["performance", "accessibility", "best-practices", "seo"]
                )

                json_path = self._save_api_result(json_result, route_key)
                json_paths.append(json_path)

            # Обработка и сохранение результатов
            process_and_save_results(json_paths, route_key, device_type, google_client, is_local=False)

    def run_crux_data_collection(self, route_keys: list, device_type: str):
        """
        Выполняет сбор CrUX данных (Chrome User Experience Report) для указанных роутов.
        :param route_keys: Список ключей роутов.
        :param device_type: Тип устройства (desktop или mobile).
        """
        google_client = self._initialize_google_client(False)  # Удалённый запуск
        routes = self.prepare_routes(route_keys)

        for route_key, route_url in routes:
            print(f"[DEBUG]: Сбор CrUX данных для: {route_key} ({route_url})")

            crux_data = run_lighthouse_api(
                url=route_url,
                strategy=device_type,
                mode="field"  # Режим CrUX
            )

            # Сохраняем CrUX данные в файл
            temp_dir = get_temp_dir_for_route(route_key, device_type, True)
            crux_file = os.path.join(temp_dir, "crux_data.json")
            with open(crux_file, "w", encoding="utf-8") as f:
                json.dump(crux_data, f, ensure_ascii=False, indent=2)

            print(f"[INFO]: CrUX данные сохранены для {route_key}: {crux_file}")
            # Обработка и сохранение результатов
            # process_and_save_results([crux_file], route_key, device_type, google_client, is_local=False)
            process_crux_results(crux_file, route_key, device, google_client, service.worksheet_name)


    def _keep_dir(self, route_key: str):
        temp_dir = os.path.join(self.temp_reports_dir, route_key)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _check_site_availability(self, url: str) -> bool:
        """
        Проверяет доступность сайта.
        :param url: URL сайта для проверки.
        :return: True, если сайт доступен, иначе False.
        """
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except RequestException:
            return False

    def _save_api_result(self, json_result: dict, route_key: str) -> str:
        """
        Сохраняет результат API в файл и возвращает путь.
        """
        temp_dir = self._keep_dir(route_key)
        json_path = os.path.join(temp_dir, "api_result.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        return json_path


"""Пример использования:"""
if __name__ == "__main__":
    base_url = get_base_url()  # Получаем базовый URL для текущего окружения
    iteration_count = 2  # Количество итераций можно изменить здесь
    device = "mobile"  # Тип устройства
    # device = "desktop"  # Тип устройства

    service = SpeedtestService()

    # Запуск локальных тестов
    # service.run_local_tests(["home"], device, iteration_count)

    # Запуск агрегированного API теста
    # service.run_api_aggregated_tests(["home"], device, iteration_count)

    # Запуск CrUX теста
    service.run_crux_data_collection(["home"], device)


