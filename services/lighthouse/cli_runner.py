import os
import shutil
import subprocess
import sys
from datetime import datetime

from services.lighthouse.config_lighthouse import get_temp_dir_for_route
from services.lighthouse.processor_lighthouse import parse_lighthouse_results

# Константа для команды Lighthouse
LIGHTHOUSE_CMD = shutil.which("lighthouse")
_lighthouse_checked = False  # Глобальный флаг

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


def run_local_lighthouse(route_key: str, route_url: str, iteration_count: int = 5, device: str = "desktop"):
    """
    Запускает локальный Lighthouse для одного URL.
    :param route_url: Полный URL для проверки.
    :param route_key: Ключ роута в ini
    :param iteration_count: Количество итераций.
    :param device: Тип устройства (desktop или mobile).
    """
    check_lighthouse_environment()  # Проверяем окружение

    date = datetime.now().strftime("%d-%m-%y")
    environment = os.getenv("ENVIRONMENT", "local")

    # Получаем временную директорию для роута
    temp_dir = get_temp_dir_for_route(route_key, device, is_local=True)

    results = [] # Инициализация списка результатов
    json_paths = []  # Список для хранения путей к JSON-файлам

    try:
        for iteration in range(1, iteration_count + 1):
            report_file = os.path.join(temp_dir, f"Report_CLI_{date}_{environment}_{route_key}_{str(iteration)}.json")
            command = [
                LIGHTHOUSE_CMD, route_url,
                "--output=json",
                f"--output-path={report_file}",
                "--chrome-flags=--headless --no-sandbox"
            ]
            if device == "mobile":
                command.append("--preset=mobile")
            else:
                command.append("--preset=desktop")

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