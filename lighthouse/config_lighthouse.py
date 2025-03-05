import configparser
import os

# Определяем путь к конфигурационному файлу со списком страниц для проверки
ROUTES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../test_routes.ini")

def load_routes_config():
    """Загружает список тестируемых страниц из test_routes.ini"""
    config = configparser.ConfigParser()
    config.read(ROUTES_CONFIG_PATH, encoding="utf-8")
    return config

def get_current_environment() -> str:
    """Возвращает текущее окружение."""
    config = load_routes_config()
    return config['environments']['current']


def get_base_url() -> str:
    """Возвращает базовый URL для текущего окружения."""
    env = get_current_environment()
    config = load_routes_config()
    if env not in config['base_urls']:
        raise ValueError(f"Неизвестный контур: {env}")

    return config['base_urls'][env]


def get_route(route_name: str) -> str:
    """Возвращает маршрут по имени."""
    config = load_routes_config()
    if 'routes' not in config or route_name not in config['routes']:
        raise ValueError(f"Не найден маршрут '{route_name}'")

    return config['routes'][route_name]


def get_full_url(env: str, route_name: str) -> str:
    """Возвращает полный URL, объединяя BASE_URL и PATH из конфига."""
    config = load_routes_config()
    if env not in config:
        raise ValueError(f"Неизвестный контур: {env}")
    if route_name not in config[env]:
        raise ValueError(f"Не найден маршрут '{route_name}' в контуре {env}")

    base_url = config[env]['BASE_URL']
    path = config[env][route_name]
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"