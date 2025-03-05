import subprocess
import os
import json
from lighthouse.cli_runner import run_lighthouse
from lighthouse.processor_lighthouse import parse_lighthouse_results
from lighthouse.cleaner import clean_temp_files
from lighthouse.config_lighthouse import load_routes_config

class SpeedtestService:
    def __init__(self):
        self.config = load_routes_config()
        self.base_report_dir = 'lighthouse/reports'
        self.run_id = "run_1"  # Или генерируйте уникальный идентификатор для каждого запуска
        self.report_dir = os.path.join(self.base_report_dir, self.run_id)
        os.makedirs(self.report_dir, exist_ok=True)

    def run_speedtest(self, url, iteration):
        try:
            # Запуск Lighthouse CLI
            print(f"Запуск теста скорости для: {url}, итерация: {iteration}")
            report_file = os.path.join(self.report_dir, f"report_{iteration}_{url.replace('http://', '').replace('https://', '').replace('/', '_')}.json")
            run_lighthouse(url, report_file)

            # Обработка результатов
            print(f"Обработка результатов для: {report_file}")
            parsed_results = parse_lighthouse_results(report_file)

            return parsed_results
        except Exception as e:
            print(f"Ошибка при выполнении теста: {e}")
            return None
        finally:
            # Очистка временных файлов
            clean_temp_files(self.report_dir)

if __name__ == "__main__":
    service = SpeedtestService()
    routes = service.config.sections()  # Получаем все контуры
    for route in routes:
        url = service.config[route]['BASE_URL']  # Получаем базовый URL
        for iteration in range(1, 6):  # Пример: 5 итераций
            results = service.run_speedtest(url, iteration)
            if results:
                print("Результаты теста:", json.dumps(results, indent=4))
