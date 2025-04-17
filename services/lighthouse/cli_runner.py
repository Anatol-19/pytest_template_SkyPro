import json
import os
import shutil
import subprocess
from datetime import datetime

from services.lighthouse.configs.config_lighthouse import get_temp_dir_for_route
from services.lighthouse.processor_lighthouse import parse_lighthouse_results


LIGHTHOUSE_CMD = shutil.which("lighthouse") # Константа для команды Lighthouse
_lighthouse_checked = False  # Глобальный флаг
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")

def check_lighthouse_environment():
    """
    Проверяет возможность работы с локальным Lighthouse,
    установлен ли Lighthouse CLI. Если нет, проверяет npm и node.
    :raises RuntimeError: Если Lighthouse не установлен или виртуальное окружение не активно.
    """
    global _lighthouse_checked
    if _lighthouse_checked:
        return  # Проверка уже выполнена

    # Проверка наличия Lighthouse
    if LIGHTHOUSE_CMD is None:
        raise RuntimeError("Lighthouse не найден в системном пути. Установите его командой: npm install -g lighthouse \n Проверяем наличие npm...")

    try:
        result = subprocess.run([LIGHTHOUSE_CMD, "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            check_npm_environment()
            raise RuntimeError("Lighthouse установлен некорректно или недоступен.")
        print(f"Lighthouse установлен: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ошибка при проверке Lighthouse: {e.stderr}")

    # Проверка активности виртуального окружения
    # if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    #     raise RuntimeError("Виртуальное окружение не активно. Активируйте его перед запуском.")

    _lighthouse_checked = True  # Устанавливаем флаг

def check_npm_environment():
    """
    Проверяет наличие npm и Node.js.
    :raises RuntimeError: Если npm или Node.js не установлены.
    """
    # Если Lighthouse не установлен, проверяем npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"npm установлен: {result.stdout.strip()}")
        else:
            raise RuntimeError("npm не установлен или недоступен.")
    except Exception as e:
        raise RuntimeError(f"Ошибка при проверке npm: {e}")

    # Если npm не установлен, проверяем наличие Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Node.js установлен: {result.stdout.strip()}")
        else:
            raise RuntimeError("Node.js не установлен или недоступен.")
    except Exception as e:
        raise RuntimeError(f"Ошибка при проверке Node.js: {e}")

def load_device_config(device: str) -> dict | None:
    """
    Загружает конфигурацию для указанного устройства (desktop или mobile).
    Если конфигурация отсутствует, возвращает None.
    :param device: Тип устройства (desktop или mobile).
    :return: Словарь с конфигурацией или None.
    """
    config_file = os.path.join(CONFIG_DIR, f"config_{device}.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке конфигурации устройства '{device}': {e}")
    return None


def run_local_lighthouse(
        route_key: str,
        route_url: str,
        iteration_count: int = 5,
        device: str = "desktop",
        mode: str = "navigation",
        categories: list = None,
        user_agent: str = None,
        strategy: str = None):
    """
    Запускает локальный Lighthouse для одного URL с параметрами.
    :param route_key: Ключ роута.
    :param route_url: Полный URL для проверки.
    :param iteration_count: Количество итераций.
    :param device: Тип устройства (desktop или mobile).
    :param mode: Режим запуска (navigation, timespan, snapshot).
    :param categories: Список категорий (performance, accessibility, best-practices, seo).
    :param user_agent: Пользовательский User-Agent.
    :param strategy: Стратегия (desktop, mobile).
    """
    check_lighthouse_environment()  # Проверяем окружение

    # Устанавливаем категории по умолчанию, если они не указаны
    if categories is None:
        categories = ["performance", "accessibility", "best-practices", "seo"]

    # Получаем временную директорию для роута
    temp_dir = get_temp_dir_for_route(route_key, device)

    results = [] # Инициализация списка результатов
    json_paths = []  # Список для хранения путей к JSON-файлам

    date = datetime.now().strftime("%d-%m-%y")
    date_time = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    environment = os.getenv("ENVIRONMENT", "local")

    # Загружаем конфигурацию устройства
    config = load_device_config(device)
    if config:
        print(f"[INFO] Используется конфигурация для устройства: {device}")
        preset = config.get("settings", {}).get("formFactor", "desktop")
        screen_emulation = config.get("settings", {}).get("screenEmulation", {})
        throttling = config.get("settings", {}).get("throttling", {})
        throttling_method = config.get("settings", {}).get("throttlingMethod", "simulate")
    else:
        print(f"[WARNING] Конфигурация для устройства '{device}' не найдена. Используются дефолтные параметры.")
        preset = "perf" if device == "mobile" else "desktop"
        screen_emulation = {}
        throttling = {}
        throttling_method = "simulate"
        user_agent = "Mozilla/5.0"
        strategy = "desktop"

    try:
        for iteration in range(1, iteration_count + 1):
            report_file = os.path.join(temp_dir, f"Report_CLI_{date}_{environment}_{route_key}_{str(iteration)}.json")
            command = [
            "lighthouse", route_url,
            "--output=json", f"--output-path={report_file}",
            "--chrome-flags=--headless --no-sandbox",
            f"--preset={preset}",
            f"--emulated-form-factor={device}",
            f"--throttling-method={throttling_method}",
            f"--mode={mode}",
            f"--only-categories={','.join(categories)}"
        ]
            # Устанавливаем флаг preset



            # Добавляем параметры эмуляции экрана, если они указаны в конфигурации
            if screen_emulation:
                if "width" in screen_emulation:
                    command.append(f"--emulated-screen-width={screen_emulation['width']}")
                if "height" in screen_emulation:
                    command.append(f"--emulated-screen-height={screen_emulation['height']}")
                if "deviceScaleRatio" in screen_emulation:
                    command.append(f"--emulated-device-scale-factor={screen_emulation['deviceScaleRatio']}")

            # Добавляем параметры, если они заданы
            if user_agent:
                command.append(f"--extra-headers=\"User-Agent: {user_agent}\"")
            if throttling_method:
                command.append(f"--throttling-method={throttling_method}")
            if throttling:
                for key, value in throttling.items():
                    command.append(f"--throttling.{key}={value}")
            if strategy:
                command.append(f"--strategy={strategy}")

            print(f"Запуск Lighthouse для: {route_url} - {device}, итерация: {str(iteration)}")
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                raise RuntimeError(f"Ошибка при запуске Lighthouse: {result.stderr}")

            if not os.path.exists(report_file):
                print(f"Файл отчета не найден: {report_file}")
                continue

            print(f"Обработка результатов для: {report_file}")
            json_paths.append(report_file)  # Добавляем путь к файлу в список
            parsed_results = parse_lighthouse_results(report_file)
            results.append(parsed_results)

    except Exception as e:
        print(f"Ошибка при выполнении теста для {route_key}: {e}")

    return json_paths