"""
Модуль для локального запуска Lighthouse через CLI.
Отвечает за:
    - Проверку наличия Lighthouse CLI
    - Формирование командной строки для запуска
    - Запуск Lighthouse и сохранение отчётов
"""

import json
import os
import shutil
import subprocess
from datetime import datetime

from services.lighthouse.configs.config_lighthouse import get_temp_dir_for_route
from services.lighthouse.processor_lighthouse import parse_lighthouse_results

# 📌 Ищем путь к установленному Lighthouse CLI
LIGHTHOUSE_CMD = shutil.which("lighthouse")
_lighthouse_checked = False  # Флаг, чтобы проверять окружение только один раз
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")


def check_lighthouse_environment():
    """
    Проверяет, установлен ли Lighthouse CLI и работает ли npm/node.
    """
    global _lighthouse_checked
    if _lighthouse_checked:
        return  # Проверка уже была

    if LIGHTHOUSE_CMD is None:
        raise RuntimeError("❌ Lighthouse не найден в PATH. Установите его: npm install -g lighthouse")

    try:
        result = subprocess.run([LIGHTHOUSE_CMD, "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            check_npm_environment()
            raise RuntimeError("❌ Lighthouse установлен некорректно или недоступен.")
        print(f"[INFO] Lighthouse установлен: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[ERROR] Ошибка при проверке Lighthouse: {e.stderr}")

    _lighthouse_checked = True


def check_npm_environment():
    """
    Проверяет наличие npm и Node.js в системе.
    """
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[INFO] npm установлен: {result.stdout.strip()}")
        else:
            raise RuntimeError("❌ npm не установлен.")
    except Exception as e:
        raise RuntimeError(f"[ERROR] Ошибка при проверке npm: {e}")

    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[INFO] Node.js установлен: {result.stdout.strip()}")
        else:
            raise RuntimeError("❌ Node.js не установлен.")
    except Exception as e:
        raise RuntimeError(f"[ERROR] Ошибка при проверке Node.js: {e}")


def load_device_config(device: str) -> dict | None:
    """
    Загружает конфигурацию эмуляции устройства (desktop или mobile).
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
    Запускает Lighthouse CLI для указанного роута с заданными параметрами.

    :param route_key: Ключ роута.
    :param route_url: Полный URL.
    :param iteration_count: Количество прогонов.
    :param device: Тип устройства ("desktop" или "mobile").
    :param mode: Режим работы Lighthouse.
    :param categories: Список категорий для анализа.
    :param user_agent: Пользовательский агент для эмуляции.
    :param strategy: Стратегия тестирования ("desktop" или "mobile").
    :return: Список путей к JSON-отчётам.
    """
    check_lighthouse_environment()

    # Категории по умолчанию
    if categories is None:
        categories = ["performance", "accessibility", "best-practices", "seo"]

    # Создаём временную директорию для отчетов
    temp_dir = get_temp_dir_for_route(route_key, device, prefix="CLI")

    results = []
    json_paths = []

    date = datetime.now().strftime("%d-%m-%y")
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
        preset = "desktop"
        screen_emulation = {}
        throttling = {}
        throttling_method = "simulate"

    try:
        for iteration in range(1, iteration_count + 1):
            report_file = os.path.join(temp_dir, f"Report_CLI_{date}_{environment}_{route_key}_iter_{iteration}.json")

            # Формируем базовую команду
            command = [
                LIGHTHOUSE_CMD, route_url,
                "--output=json",
                f"--output-path={report_file}",
                "--chrome-flags=--headless --no-sandbox",
                f"--preset={preset}",
                f"--emulated-form-factor={device}",
                f"--throttling-method={throttling_method}",
                f"--mode={mode}",
                f"--only-categories={','.join(categories)}"
            ]

            # Параметры эмуляции экрана
            if screen_emulation:
                if "width" in screen_emulation:
                    command.append(f"--emulated-screen-width={screen_emulation['width']}")
                if "height" in screen_emulation:
                    command.append(f"--emulated-screen-height={screen_emulation['height']}")
                if "deviceScaleRatio" in screen_emulation:
                    command.append(f"--emulated-device-scale-factor={screen_emulation['deviceScaleRatio']}")

            # Дополнительные параметры
            if user_agent:
                command.append(f"--extra-headers=\"User-Agent: {user_agent}\"")
            if throttling:
                for key, value in throttling.items():
                    command.append(f"--throttling.{key}={value}")
            if strategy:
                command.append(f"--strategy={strategy}")

            print(f"[INFO] Запуск Lighthouse для: {route_url} - {device}, итерация {iteration}")
            print(f"[DEBUG] Команда: {' '.join(command)}")

            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[ERROR] Ошибка Lighthouse: {result.stderr}")
                raise RuntimeError(f"Ошибка при запуске Lighthouse для {route_key}")

            if not os.path.exists(report_file):
                print(f"[ERROR] Файл отчета не найден после итерации {iteration}: {report_file}")
                continue

            json_paths.append(report_file)
            parsed_results = parse_lighthouse_results(report_file)
            results.append(parsed_results)

    except Exception as e:
        print(f"[ERROR] Ошибка при выполнении теста для {route_key}: {e}")

    return json_paths
