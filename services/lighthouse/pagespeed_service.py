"""

Модуль для выполнения тестов скорости с использованием Lighthouse.

"""

import json

import os

import pytest

import sys

from datetime import datetime

from typing import Optional, Tuple, List, Literal

import requests

from dotenv import load_dotenv

from google.auth.exceptions import RefreshError

from requests import RequestException

from services.lighthouse.api_runner import run_api_lighthouse

from services.lighthouse.processor_lighthouse import process_and_save_results, process_crux_results

# Добавляем корневую директорию проекта в sys.path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.google.google_sheets_client import GoogleSheetsClient

from services.lighthouse.cli_runner import run_local_lighthouse

from services.lighthouse.configs.config_lighthouse import (

    get_route, get_base_url, load_routes_config, get_full_url,

    get_current_environment, resolve_worksheet_name, REPORTS_DIR,

    TEMP_REPORTS_DIR, ensure_directories_exist, get_temp_dir_for_route,

    get_google_creds_path

)

# Загружаем .env из папки lighthouse/configs

dotenv_path = os.path.join(os.path.dirname(__file__), 'configs', 'config_lighthouse.env')

load_dotenv(dotenv_path)

def _save_api_result(json_result: dict, route_key: str, device_type: str) -> str:

    """

    Сохраняет результат API в файл и возвращает путь.

    """

    temp_dir = get_temp_dir_for_route(route_key, device_type)

    json_path = os.path.join(temp_dir, "api_result.json")

    with open(json_path, "w", encoding="utf-8") as f:

        json.dump(json_result, f, ensure_ascii=False, indent=2)

    return json_path

def _check_site_availability(url: str) -> bool:

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

def prepare_routes(route_keys: List[str], base_url: Optional[str] = None) -> List[Tuple[str, str]]:

    """

    Подготавливает пары (route_key, full_url). Позволяет вручную передавать base_url.

    """

    if base_url is None:

        base_url = get_base_url().rstrip("/")

    else:

        base_url = base_url.rstrip("/")

    routes = []

    for key in route_keys:

        route_path = get_route(key)

        full_url = f"{base_url}{route_path}"

        routes.append((key, full_url))

    return routes

@pytest.mark.skip(reason="Класс предназначен не для тестов")

class SpeedtestService:

    """

    Класс для выполнения тестов скорости и обработки результатов.

    Отвечает за orchestration CLI, API и CrUX запусков.

    """

    iteration_counter = 0

    def __init__(self, reports_dir=REPORTS_DIR, temp_reports_dir=TEMP_REPORTS_DIR,
                 environment: Optional[str] = None):
        """Инициализирует объект SpeedtestService.

        Args:
            environment: Явно заданный контур. Если None — читается из base_urls.ini.
                         Рекомендуется передавать явно при параллельных запусках.
        """
        SpeedtestService.iteration_counter += 1
        self.iteration = SpeedtestService.iteration_counter

        self.base_reports_dir = reports_dir
        self.temp_reports_dir = temp_reports_dir
        ensure_directories_exist()

        self.config = load_routes_config()
        self.date = datetime.now().strftime("%d-%m-%y")
        self.dateTime = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        self.environment = environment or get_current_environment()
        self.worksheet_name: str

    def _initialize_google_client(self, source: Literal["cli", "api", "crux"]) -> GoogleSheetsClient:

        """

        Инициализирует клиента Google Sheets.

        """

        credentials_path = get_google_creds_path()

        spreadsheet_id = os.getenv("GS_SHEET_ID")

        self.worksheet_name = resolve_worksheet_name(self.environment, source)

        if not spreadsheet_id:

            raise RuntimeError("[ERROR] Не установлены переменные окружения для Google Sheets")

        try:

            return GoogleSheetsClient(

                credentials_path=str(credentials_path),

                spreadsheet_id=spreadsheet_id,

                worksheet_name=self.worksheet_name

            )

        except RefreshError as e:

            print(f"[ERROR] Ошибка аутентификации: {e}")

            raise

    def _get_routes_from_config(self) -> List[str]:

        """

        Загружает список ключей роутов из routes.ini.

        """

        if "routes" not in self.config:

            raise ValueError("Секция [routes] не найдена в routes.ini")

        return list(self.config["routes"].keys())

    def run_local_tests(self, route_keys: Optional[List[str]], device_type: str,

                        n_iteration: int = 10, keep_temp_files: bool = False,

                        base_url: Optional[str] = None):

        """

        Выполняет тесты с использованием локального Lighthouse CLI.

        """

        google_client = self._initialize_google_client("cli")

        base_url = base_url or get_base_url()

        route_keys = route_keys or self._get_routes_from_config()

        routes = prepare_routes(route_keys, base_url=base_url)

        for route_key, route_url in routes:
            print(f"[DEBUG]: Перед запуском: {route_key} — {route_url}")
            if not _check_site_availability(route_url):
                print(f"[ERROR] {route_url} недоступен — пропуск.")
                continue

            json_paths = run_local_lighthouse(route_key, route_url, n_iteration, device_type)
            process_and_save_results(json_paths, route_key, device_type, google_client,
                                     is_local=True, keep_temp_files=keep_temp_files,
                                     environment=self.environment, full_url=route_url)

        google_client.flush()

    def run_api_aggregated_tests(self, route_keys: Optional[List[str]], device_type: str,

                                 n_iteration: int = 10, keep_temp_files: bool = False,

                                 base_url: Optional[str] = None):

        """

        Выполняет запуск Lighthouse через PageSpeed API с агрегацией.

        """

        google_client = self._initialize_google_client("api")

        base_url = base_url or get_base_url()

        route_keys = route_keys or self._get_routes_from_config()

        routes = prepare_routes(route_keys, base_url=base_url)

        for route_key, route_url in routes:

            print(f"[DEBUG]: API запуск для {route_key}: {route_url}")

            temp_dir = get_temp_dir_for_route(route_key, device_type, prefix="API")

            json_paths = []

            for iteration in range(1, n_iteration + 1):

                json_result = run_api_lighthouse(

                    url=route_url,

                    strategy=device_type,

                    categories=["performance", "accessibility", "best-practices", "seo"]

                )

                if not json_result:

                    print(f"[WARNING] Итерация {iteration} без данных: {route_key}")

                    continue

                json_path = os.path.join(temp_dir, f"Report_API_{iteration}.json")

                with open(json_path, "w", encoding="utf-8") as f:

                    json.dump(json_result, f, ensure_ascii=False, indent=2)

                json_paths.append(json_path)

            process_and_save_results(json_paths, route_key, device_type, google_client,
                                     is_local=False, keep_temp_files=keep_temp_files,
                                     environment=self.environment, full_url=route_url)

        google_client.flush()

    def run_crux_data_collection(self, route_keys: Optional[List[str]], device_type: str,
                                 base_url: Optional[str] = None,
                                 include_origin: bool = False):
        """Выполняет сбор CrUX: page (field) + опционально origin по каждому роуту и девайсу."""
        google_client = self._initialize_google_client("crux")
        base_url = base_url or get_base_url()
        route_keys = route_keys or self._get_routes_from_config()
        routes = prepare_routes(route_keys, base_url=base_url)

        for route_key, route_url in routes:
            print(f"[DEBUG]: CrUX для {route_key}: {route_url}")

            # URL-level (page) field data
            crux_data_url = run_api_lighthouse(
                url=route_url,
                strategy=device_type,
                mode="field"
            )
            temp_dir_url = get_temp_dir_for_route(route_key, device_type, prefix="CrUX")
            crux_file_url = os.path.join(temp_dir_url, "crux_data.json")
            with open(crux_file_url, "w", encoding="utf-8") as f:
                json.dump(crux_data_url, f, ensure_ascii=False, indent=2)
            print(f"[INFO]: CrUX (page) сохранен: {crux_file_url}")
            process_crux_results(
                crux_file_url,
                route_key,
                device_type,
                google_client,
                full_url_override=route_url,
                route_label=route_key,
                environment=self.environment,
            )

            if include_origin:
                origin_url = base_url.rstrip('/')
                print(f"[DEBUG]: CrUX origin для {route_key}: {origin_url}")
                crux_data_origin = run_api_lighthouse(
                    url=origin_url,
                    strategy=device_type,
                    mode="origin"
                )
                temp_dir_origin = get_temp_dir_for_route(route_key + "_origin", device_type, prefix="CrUX")
                crux_file_origin = os.path.join(temp_dir_origin, "crux_origin_data.json")
                with open(crux_file_origin, "w", encoding="utf-8") as f:
                    json.dump(crux_data_origin, f, ensure_ascii=False, indent=2)
                print(f"[INFO]: CrUX (origin) сохранен: {crux_file_origin}")
                process_crux_results(
                    crux_file_origin,
                    route_key,
                    device_type,
                    google_client,
                    full_url_override=origin_url,
                    route_label=f"{route_key} (origin)",
                    environment=self.environment,
                )

        google_client.flush()

if __name__ == "__main__":

    base_url = get_base_url()

    iteration_count = 10

    device = "desktop"

    service = SpeedtestService()

    # Пример вызовов:

    service.run_local_tests(["home"], device, iteration_count)

    # service.run_api_aggregated_tests(["home"], device, iteration_count)

    # service.run_crux_data_collection(["home"], device)
