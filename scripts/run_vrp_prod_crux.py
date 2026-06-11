"""Запуск CrUX по всем роутам для VRP_PROD — оба устройства."""
import sys
import os
from datetime import datetime

# Логирование в файл
LOG_DIR = os.path.join(os.path.dirname(__file__), "Reports", "reports_lighthouse")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"run_vrp_prod_crux_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    # Используем encode errors='replace' для Unicode символов
    try:
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except UnicodeEncodeError:
        # Заменяем проблемные символы
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

def run_crux_collection(environment: str):
    log(f"\n=== CrUX сбор: {environment} ===")
    log(f"Лог файл: {log_file}")
    service = SpeedtestService(environment=environment)
    
    for device in DEVICES:
        log(f"-- {environment} CrUX ({device}): все роуты")
        try:
            service.run_crux_data_collection(
                route_keys=None,  # все роуты
                device_type=device,
                base_url=None,
                include_origin=False,  # только page-level данные
                tag="",  # возьмётся из dashboard
                sprint=""  # возьмётся из dashboard
            )
            log(f"[OK] {environment} CrUX ({device}) завершён")
        except Exception as e:
            log(f"[ERROR] {environment} CrUX ({device}) ошибка: {e}")

if __name__ == "__main__":
    try:
        run_crux_collection("VRP_PROD")
        log("\n=== Завершение CrUX VRP_PROD ===")
    except Exception as e:
        log(f"\n=== Критическая ошибка: {e} ===")
        raise
