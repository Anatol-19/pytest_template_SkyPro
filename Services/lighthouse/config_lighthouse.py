import configparser
import os


# Определяем путь к конфигурационному файлу со списком страниц для проверки
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../URLs/base_urls.ini")
ROUTES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../URLs/routes.ini")
print("Ищу конфиг по пути:", CONFIG_PATH)


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
    config = configparser.ConfigParser()

    print("Ищу конфиг по пути:", CONFIG_PATH)  # Выведет путь
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Файл конфигурации не найден: {CONFIG_PATH}")

    config.read(CONFIG_PATH, encoding="utf-8")
    print("Загруженные секции:", config.sections())  # 🔍 Отладка. Проверим, загружены ли данные

    if "environments" not in config or "current" not in config["environments"]:
        raise KeyError("Отсутствует секция [environments] или ключ 'current' в base_urls.ini")

    current_env = config["environments"]["current"]

    if current_env not in config:
        raise KeyError(f"Контур '{current_env}' не найден в base_urls.ini")

    return config[current_env]["BASE_URL"]


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
    return f"{get_base_url().rstrip('/')}{get_route(route_name)}"