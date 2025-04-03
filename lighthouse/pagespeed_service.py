import sys
import shutil
import subprocess
import json
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from lighthouse.cleaner import clean_temp_files
from lighthouse.cli_runner import run_lighthouse
from lighthouse.config_lighthouse import get_base_url, get_route, load_routes_config, get_full_url, \
    get_current_environment
from lighthouse.processor_lighthouse import parse_lighthouse_results, save_aggregated_results_to_csv, aggregate_results


def is_lighthouse_installed():
    """Проверяет, установлен ли Lighthouse CLI. Если нет, проверяет npm и node."""
    # Проверка установки Lighthouse
    lighthouse_cmd = shutil.which("lighthouse")
    if lighthouse_cmd is not None:
        try:
            result = subprocess.run([lighthouse_cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Lighthouse установлен: {result.stdout.strip()}")
                return True
            else:
                print("Lighthouse не установлен или не доступен.")
        except Exception as e:
            print(f"Ошибка при проверке Lighthouse: {e}")
            return False

    # Если Lighthouse не установлен, проверяем npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"npm установлен: {result.stdout.strip()}")
        else:
            print("npm не установлен или не доступен.")
            return False
    except Exception as e:
        print(f"Ошибка при проверке npm: {e}")
        return False

    # Если npm не установлен, проверяем node
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Node.js установлен: {result.stdout.strip()}")
        else:
            print("Node.js не установлен или не доступен.")
            return False
    except Exception as e:
        print(f"Ошибка при проверке Node.js: {e}")
        return False

    return False  # Если ничего не установлено, возвращаем False

def is_virtualenv_active() -> bool:
    """Проверяет, активно ли виртуальное окружение."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

class SpeedtestService:
    iteration_counter = 0
    def __init__(self):
        SpeedtestService.iteration_counter += 1
        self.iteration = SpeedtestService.iteration_counter
        self.config = load_routes_config()
        self.base_report_dir = 'lighthouse/reports'
        self.temp_report_dir = 'lighthouse/temp_reports'
        self.date = datetime.now().strftime("%d-%m-%y")
        self.dateTime = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        self.environment = get_current_environment()
        if not is_lighthouse_installed():
            is_virtualenv_active()
            raise RuntimeError("Lighthouse не установлен! Установите его командой: npm install -g lighthouse")

    def run_speedtest(self, page_url, route_name, iteration_count):
        results = []
        temp_dir = os.path.join(self.temp_report_dir, f"{self.date}_{self.environment}_{route_name}")
        os.makedirs(temp_dir, exist_ok=True)

        for iteration in range(1, iteration_count + 1):
            report_file = os.path.join(temp_dir, f"report_{self.dateTime}_{self.environment}_{route_name}_{iteration}.json")

            try:
                print(f"Запуск теста скорости для: {page_url}, итерация: {iteration}")
                # ToDO контура флагами или переменной
                run_lighthouse(page_url, "desktop", report_file)
                if not os.path.exists(report_file):
                    print(f"Файл отчета не найден: {report_file}")
                    continue

                print(f"Обработка результатов для: {report_file}")
                parsed_results = parse_lighthouse_results(report_file)
                results.append(parsed_results)
            except Exception as e:
                print(f"Ошибка при выполнении теста: {e}")

        if results:
            aggregated_results = aggregate_results(results)
            output_csv = os.path.join(self.base_report_dir, f"aggregated_results_{self.date}_{self.environment}_{route_name}.csv")
            save_aggregated_results_to_csv(aggregated_results, output_csv)
            print(f"Агрегированные результаты сохранены в: {output_csv}")

        print("Очистка временных файлов ! ! !")
        clean_temp_files(temp_dir)

if __name__ == "__main__":
    service = SpeedtestService()
    base_url = get_base_url()  # Получаем базовый URL для текущего окружения
    routes = service.config.options('routes')  # Получаем все ключи в секции 'routes'
    iteration_count = 5  # Количество итераций можно изменить здесь

    for route in routes:
        full_url = get_full_url(route)
        service.run_speedtest(full_url, route, iteration_count)