import shutil
import subprocess
import os
import json
from datetime import datetime

from lighthouse.cleaner import clean_temp_files
from lighthouse.cli_runner import run_lighthouse
from lighthouse.config_lighthouse import load_routes_config
from lighthouse.processor_lighthouse import parse_lighthouse_results


def is_lighthouse_installed():
    """Проверяет, установлен ли Lighthouse CLI."""
    # try:
    #     result = subprocess.run(["lighthouse", "--version"], capture_output=True, text=True)
    #     return result.returncode == 0
    # except FileNotFoundError:
    #     return False
    return shutil.which("lighthouse") is not None

class SpeedtestService:
    iteration_counter = 0
    def __init__(self):
        SpeedtestService.iteration_counter += 1
        self.iteration = SpeedtestService.iteration_counter
        self.config = load_routes_config()
        self.base_report_dir = 'lighthouse/reports'
        self.date = datetime.now().strftime("%d-%m-%y")
        self.run_id = f"{self.date}-run_{self.iteration}"
        self.report_dir = os.path.join(self.base_report_dir, self.run_id)
        os.makedirs(self.report_dir, exist_ok=True)
        if not is_lighthouse_installed():
            raise RuntimeError("Lighthouse не установлен! Установите его командой: npm install -g lighthouse")

    def cleanup(self):
        print("Очистка временных файлов ! ! !")
        clean_temp_files(self.report_dir)

    def run_speedtest(self, page_url, iteration_count):
        try:
            # Запуск Lighthouse CLI
            print(f"Запуск теста скорости для: {page_url}, итерация: {iteration_count}")
            report_file = os.path.join(self.report_dir, f"report_{iteration_count}.json")

            # Сначала запускаем тест
            # ToDO контура флагами или переменной
            run_lighthouse(page_url, "desktop", report_file)
            # Потом проверяем, что отчет создан
            if not os.path.exists(report_file):
                print(f"Файл отчета не найден: {report_file}")
                return None

            # Обработка результатов
            print(f"Обработка результатов для: {report_file}")
            parsed_results = parse_lighthouse_results(report_file)
            return parsed_results
        except Exception as e:
            print(f"Ошибка при выполнении теста: {e}")
            return None

if __name__ == "__main__":
    service = SpeedtestService()
    routes = service.config.sections()  # Получаем все контуры
    for route in routes:
        url = service.config[route]['BASE_URL']  # Получаем базовый URL
        for iteration in range(1, 6):  # Пример: 5 итераций
            results = service.run_speedtest(url, iteration)
            if results:
                print("Результаты теста:", json.dumps(results, indent=4))
                service.cleanup()   # Очистка временных файлов
