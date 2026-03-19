import configparser
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

# Глобальная переменная
BASE_URL = None # Глобальный кэш base_url

# === 📁 Путь и директории проекта ===
ROOT_DIR = Path(__file__).resolve().parents[3]              # Определяем корневую директорию проекта
LIGHTHOUSE_DIR = ROOT_DIR / "services" / "lighthouse"       # Папка lighthouse
URLS_DIR = ROOT_DIR / "URLs"                                # Папка URLs
REPORTS_DIR = ROOT_DIR / "Reports" / "reports_lighthouse"   # Пути для хранения отчетов
TEMP_REPORTS_DIR = REPORTS_DIR  / "temp_lighthouse"         # Пути для хранения временных отчетов

# Определяем путь к конфигурационному файлу со списком страниц для проверки
CONFIG_PATH = URLS_DIR / "base_urls.ini"
ROUTES_CONFIG_PATH = URLS_DIR / "routes.ini"

# Названия шаблонных листов в Google Sheets для разных типов запусков
TEMPLATE_SHEETS = {
    "cli": "_CLI_Template",
    "api": "_API_Template",
    "crux": "_ChU_Template",
}

print("[INFO] Ищу конфиг по пути:", CONFIG_PATH)
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"[ERROR] Файл конфигурации не найден: {CONFIG_PATH}")


def ensure_directories_exist():
    """ Убедиться, что все необходимые директории существуют."""
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Директории для отчетов и временных файлов проверены/созданы.")
    except Exception as e:
        raise RuntimeError(f"[ERROR] Ошибка при создании директорий: {e}")


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


def _load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"[ERROR] Файл конфигурации не найден: {CONFIG_PATH}")
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    return config


def get_base_url(environment: str | None = None) -> str:
    """
    Получает BASE_URL.

    Args:
        environment: необязательное имя контура. Если передано, берём URL из секции env без смены
                     `environments.current`. Это позволяет гонять несколько процессов параллельно,
                     не перезаписывая base_urls.ini. Если не передано — используем "current" + кеш BASE_URL.
    :raises FileNotFoundError: Если файл конфигурации не найден.
    :raises KeyError: Если отсутствует секция или контур.
    """
    global BASE_URL

    if environment:
        config = _load_config()
        if environment not in config:
            raise KeyError(f"[ERROR] В base_urls.ini нет секции '{environment}'")
        return config[environment]["BASE_URL"]

    if BASE_URL is None:
        config = _load_config()

        if "environments" not in config or "current" not in config["environments"]:
            raise KeyError("[ERROR] Отсутствует секция [environments] или ключ 'current' в base_urls.ini")

        current_env = config["environments"]["current"]
        if current_env not in config:
            raise KeyError(f"[ERROR] Контур '{current_env}' не найден в base_urls.ini")

        BASE_URL = config[current_env]["BASE_URL"]
        print(f"[DEBUG] Указанный контур: {current_env} - {BASE_URL}")  # 🔍 Отладка. Проверим, загружены ли данные

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


def get_temp_dir_for_route(route_key: str, device: str, prefix: str = "CLI") -> Path:
    """
    Возвращает путь к временной директории для конкретного роута и устройства.
    :param route_key: Ключ роута.
    :param device: Тип устройства (desktop или mobile).
    :param prefix: Тип запуска ("CLI", "API", "CrUX").
    :return: Путь к временной директории.
    """
    date = datetime.now().strftime("%d-%m-%y")
    temp_dir = TEMP_REPORTS_DIR / f"{date}_{prefix}_{route_key}_{device}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG] Временная директория для роута {route_key} создана: {temp_dir}")
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
    """Удаляет директорию с временными файлами."""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"[INFO] Временные файлы удалены: {temp_dir}")


def clean_temp_files(temp_dir: str):
    """Удаляет временные файлы (строковая версия)."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Временные файлы в {temp_dir} были удалены.")
    else:
        print(f"Директория {temp_dir} не существует, ничего не удалено.")


def get_google_creds_path() -> Path:
    """
    Возвращает абсолютный путь к файлу учетных данных Google -путь до файла с ключом сервисного аккаунта из переменной окружения GS_CREDS.
    :return: Абсолютный путь к файлу учетных данных.
    :raises ValueError: Если переменная окружения GS_CREDS не задана.
    """
    gs_creds = os.getenv("GS_CREDS")
    if not gs_creds:
        raise ValueError("Переменная окружения 'GS_CREDS' не задана.")

    creds_path = Path(gs_creds)
    if not creds_path.is_absolute():
        creds_path = ROOT_DIR / creds_path

    if not creds_path.exists():
        raise FileNotFoundError(f"[ERROR] Файл учетных данных не найден: {creds_path}")

    return creds_path


def resolve_worksheet_name(environment: str, source: Literal["cli", "api", "crux"]) -> str:
    """
    Возвращает имя рабочего листа Google Sheets по окружению и источнику.
    
    Структура вкладок:
    - CrUX - общее по всем проектам
    - VRP [PROD], VRS [PROD] - CLI и API в одном листе, колонка Type
    - VRP [STAGE], VRP [TEST], VRP [DEV] - только CLI
    - VRS [STAGE], VRS [TEST], VRS [DEV] - только CLI
    - Config - управление автоформатированием
    """
    # CrUX всегда отдельный лист
    if source == "crux":
        return "CrUX"
    
    # Парсим environment: VRP_PROD -> project=VRP, env=PROD
    env_upper = environment.upper()
    
    if "_" in environment:
        parts = environment.split("_", 1)
        project = parts[0].upper()
        env = parts[1].upper()
    else:
        project = environment.upper()
        env = "PROD"
    
    # Формируем имя листа
    # PROD -> "VRP [PROD]", "VRS [PROD]"
    # STAGE -> "VRP [STAGE]", "VRS [STAGE]"
    # TEST -> "VRP [TEST]", "VRS [TEST]"
    # DEV -> "VRP [DEV]", "VRS [DEV]"
    
    return f"{project} [{env}]"
