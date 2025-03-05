import os
import shutil

def clean_temp_files(report_dir: str):
    """Удаляет временные файлы из директории отчетов."""
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)
        print(f"Временные файлы в {report_dir} были удалены.")
    else:
        print(f"Директория {report_dir} не существует, ничего не удалено.")
