"""Запуск сатурации VRP_PROD — все роуты, оба устройства (CLI + API)."""
import sys
import os
from datetime import datetime

# Логирование в файл
LOG_DIR = os.path.join(os.path.dirname(__file__), "Reports", "reports_lighthouse")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"run_vrp_prod_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except UnicodeEncodeError:
        safe_line = line.encode('cp1251', errors='replace').decode('cp1251')
        print(safe_line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(safe_line + "\n")

# Перенаправляем stdout в лог
original_stdout = sys.stdout
class TeeOutput:
    def write(self, text):
        original_stdout.write(text)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(text)
    def flush(self):
        original_stdout.flush()

sys.stdout = TeeOutput()

from services.lighthouse.pagespeed_service import SpeedtestService

DEVICES = ["desktop", "mobile"]

def run_cli_saturation(environment: str):
    log(f"\n=== CLI saturation: {environment} ===")
    log(f"Лог файл: {log_file}")
    service = SpeedtestService(environment=environment)
    for device in DEVICES:
        log(f"-- {environment} CLI ({device}): 10 итераций по всем роутам")
        try:
            service.run_local_tests(
                route_keys=None,
                device_type=device,
                n_iteration=10,
                tag="",
                sprint=""
            )
            log(f"[OK] {environment} CLI ({device}) завершён")
        except Exception as e:
            log(f"[ERROR] {environment} CLI ({device}) ошибка: {e}")

def run_api_saturation(environment: str):
    log(f"\n=== API saturation: {environment} ===")
    service = SpeedtestService(environment=environment)
    for device in DEVICES:
        log(f"-- {environment} API ({device}): 10 итераций по всем роутам")
        try:
            service.run_api_aggregated_tests(
                route_keys=None,
                device_type=device,
                n_iteration=10,
                tag="",
                sprint=""
            )
            log(f"[OK] {environment} API ({device}) завершён")
        except Exception as e:
            log(f"[ERROR] {environment} API ({device}) ошибка: {e}")

if __name__ == "__main__":
    try:
        run_cli_saturation("VRP_PROD")
        run_api_saturation("VRP_PROD")
        log("\n=== Завершение VRP_PROD ===")
    except Exception as e:
        log(f"\n=== Критическая ошибка: {e} ===")
        raise
