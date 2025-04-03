import os
import shutil

def clean_temp_files(temp_dir: str):
    """Удаляет временные файлы из директории отчетов."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Временные файлы в {temp_dir} были удалены.")
    else:
        print(f"Директория {temp_dir} не существует, ничего не удалено.")
