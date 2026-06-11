"""Запуск сатурации VRP_STAGE — все роуты, оба устройства (CLI)."""
import sys
import os
from datetime import datetime

# Логирование в файл
LOG_DIR = os.path.join(os.path.dirname(__file__), "Reports", "reports_lighthouse")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"run_vrp_stage_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

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
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(text)
        except UnicodeEncodeError:
            safe_text = text.encode('cp1251', errors='replace').decode('cp1251')
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(safe_text)
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
        log(f"-- {environment} ({device}): 10 итераций по всем роутам")
        try:
            service.run_local_tests(
                route_keys=None,
                device_type=device,
                n_iteration=10,
                tag="",  # возьмётся из dashboard
                sprint=""  # возьмётся из dashboard
            )
            log(f"[OK] {environment} ({device}) завершён")
        except Exception as e:
            log(f"[ERROR] {environment} ({device}) ошибка: {e}")

if __name__ == "__main__":
    try:
        run_cli_saturation("VRP_STAGE")
        log("\n=== Завершение VRP_STAGE ===")
    except Exception as e:
        log(f"\n=== Критическая ошибка: {e} ===")
        raise
