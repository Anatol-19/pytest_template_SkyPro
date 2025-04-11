import configparser
import os
import shutil
from datetime import datetime
from pathlib import Path


# Определяем путь к конфигурационному файлу со списком страниц для проверки
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../URLs/base_urls.ini"))
ROUTES_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../URLs/routes.ini"))
print("Ищу конфиг по пути:", CONFIG_PATH)
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Файл конфигурации не найден: {CONFIG_PATH}")

# Глобальная переменная
BASE_URL = None # для хранения базового URL
ROOT_DIR = Path(__file__).resolve().parents[2] # Определяем корневую директорию проекта
REPORTS_DIR = ROOT_DIR / "Reports" / "reports_lighthouse" # Пути для хранения отчетов
TEMP_REPORTS_DIR = REPORTS_DIR  / "temp_lighthouse" # Пути для хранения временных отчетов


def ensure_directories_exist():
    """ Убедиться, что все необходимые директории существуют."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_routes_config()-> configparser.ConfigParser:
    """
    Загружает список тестируемых страниц из routes.ini.
    :return: Объект ConfigParser с загруженными данными.
    """
    config = configparser.ConfigParser()
    config.read(ROUTES_CONFIG_PATH, encoding="utf-8")
    return config


def get_current_environment() -> str:
    """
    Возвращает текущее окружение.
    :return: Название текущего окружения.
    :raises KeyError: Если отсутствует секция [environments] или ключ 'current' в base_urls.ini.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    if "environments" not in config or "current" not in config["environments"]:
        raise KeyError("Отсутствует секция [environments] или ключ 'current' в base_urls.ini")
    return config["environments"]["current"]


def get_base_url() -> str:
    """
    Получает BASE_URL для текущего выбранного контура.
    :return: Базовый URL для текущего окружения.
    :raises FileNotFoundError: Если файл конфигурации не найден.
    :raises KeyError: Если отсутствует секция [environments] или ключ 'current' в base_urls.ini, или если текущий контур не найден.
    """
    global BASE_URL
    if BASE_URL is None:
        config = configparser.ConfigParser()

        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"Файл конфигурации не найден: {CONFIG_PATH}")

        config.read(CONFIG_PATH, encoding="utf-8")

        if "environments" not in config or "current" not in config["environments"]:
            raise KeyError("Отсутствует секция [environments] или ключ 'current' в base_urls.ini")

        current_env = config["environments"]["current"]
        BASE_URL = config[current_env]["BASE_URL"]
        print(f"указанный контур: {current_env} - {BASE_URL}")  # 🔍 Отладка. Проверим, загружены ли данные

        if current_env not in config:
            raise KeyError(f"Контур '{current_env}' не найден в base_urls.ini")

    return BASE_URL


def get_route(route_name: str) -> str:
    """
    Получает путь для указанного роута.
    :param route_name: Название роута.
    :return: Путь для указанного роута.
    :raises KeyError: Если роут не найден в routes.ini.
    """
    config = configparser.ConfigParser()
    config.read(ROUTES_CONFIG_PATH, encoding="utf-8")

    if "routes" not in config or route_name not in config["routes"]:
        raise KeyError(f"Роут '{route_name}' не найден в routes.ini")

    return config["routes"][route_name]


def get_full_url(route_name: str) -> str:
    """
    Формирует полный URL для указанного роута.
    :param route_name: Название роута.
    :return: Полный URL для указанного роута.
    """
    base_url = get_base_url().rstrip('/')
    route_path = get_route(route_name)
    full_url = f"{base_url}{route_path}"
    print(
        f"[DEBUG]: base_url={base_url}, route_name={route_name}, route_path={route_path}, full_url={full_url}")  # Отладка
    return full_url
    # return f"{get_base_url().rstrip('/')}{get_route(route_name)}"


def get_temp_dir_for_route(route_key: str, device: str, is_local: bool) -> Path:
    """
    Возвращает путь к временной директории для конкретного роута и устройства.
    :param route_key: Ключ роута.
    :param device: Тип устройства (desktop или mobile).
    :param is_local: Флаг, указывающий на локальный запуск.
    :return: Путь к временной директории.
    """
    date = datetime.now().strftime("%d-%m-%y")
    prefix = "local" if is_local else "api"
    temp_dir = TEMP_REPORTS_DIR / f"{date}_{prefix}_{route_key}_{device}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_report_path(route_key: str, device: str, is_local: bool) -> Path:
    """
    Возвращает путь к финальному отчету для конкретного роута и устройства.
    :param route_key: Ключ роута.
    :param device: Тип устройства (desktop или mobile).
    :param is_local: Флаг, указывающий на локальный запуск.
    :return: Путь к финальному отчету.
    """
    date_time = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    prefix = "local" if is_local else "api"
    report_path = REPORTS_DIR / f"{date_time}_{prefix}_{route_key}_{device}_report.json"
    return report_path


def cleanup_temp_files(temp_dir: Path):
    """
    Удаляет временные файлы после завершения работы.
    :param temp_dir: Путь к директории с временными файлами.
    """
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"[INFO] Временные файлы удалены: {temp_dir}")


def get_worksheet_name(environment: str, is_local: bool) -> str:
    """
    Возвращает имя листа для текущего окружения и типа запуска.
    :param environment: Название текущего окружения (например, DEV, TEST, STAGE, PROD).
    :param is_local: Флаг, указывающий на локальный запуск (True) или API (False).
    :return: Имя листа для текущего окружения и типа запуска.
    :raises KeyError: Если переменная окружения для листа не найдена.
    """
    if not is_local:
        # Для API всегда используется PROD
        worksheet_var = "GS_WORKSHEET_PROD"
    else:
        # Для локального запуска выбираем по окружению
        suffix = "_L" if environment.upper() == "PROD" else ""
        worksheet_var = f"GS_WORKSHEET_{environment.upper()}{suffix}"

    worksheet_name = os.getenv(worksheet_var)
    if not worksheet_name:
        raise KeyError(f"Переменная окружения {worksheet_var} не найдена")
    return worksheet_name