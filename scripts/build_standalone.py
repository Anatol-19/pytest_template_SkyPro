#!/usr/bin/env python3
"""
Скрипт сборки standalone-пакета Lighthouse Runner.

Копирует нужные файлы из проекта в dist/lighthouse_runner/,
патчит pagespeed_service.py (убирает pytest) и создаёт zip-архив.

Запуск:
    python scripts/build_standalone.py
"""

import os
import re
import shutil
import zipfile
from pathlib import Path

# ── Пути ──
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = DIST_DIR / "lighthouse_runner"
ZIP_PATH = DIST_DIR / "lighthouse_runner.zip"


def clean_output():
    """Удаляет предыдущую сборку (кроме run.py, requirements.txt, README.txt)."""
    # Удаляем только скопированные директории, оставляем файлы точки входа
    for subdir in ["URLs", "services"]:
        target = PACKAGE_DIR / subdir
        if target.exists():
            shutil.rmtree(target)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()


def copy_files():
    """Копирует файлы проекта в пакет."""
    copies = [
        # URLs
        ("URLs/base_urls.ini", "URLs/base_urls.ini"),
        ("URLs/routes.ini", "URLs/routes.ini"),

        # Google Sheets client
        ("services/__init__.py", "services/__init__.py"),
        ("services/google/__init__.py", "services/google/__init__.py"),
        ("services/google/google_sheets_client.py", "services/google/google_sheets_client.py"),

        # Lighthouse service
        ("services/lighthouse/__init__.py", "services/lighthouse/__init__.py"),
        ("services/lighthouse/cli_runner.py", "services/lighthouse/cli_runner.py"),
        ("services/lighthouse/api_runner.py", "services/lighthouse/api_runner.py"),
        ("services/lighthouse/processor_lighthouse.py", "services/lighthouse/processor_lighthouse.py"),
        ("services/lighthouse/pagespeed_service.py", "services/lighthouse/pagespeed_service.py"),

        # Configs
        ("services/lighthouse/configs/__init__.py", "services/lighthouse/configs/__init__.py"),
        ("services/lighthouse/configs/config_lighthouse.py", "services/lighthouse/configs/config_lighthouse.py"),
        ("services/lighthouse/configs/config_lighthouse.env", "services/lighthouse/configs/config_lighthouse.env"),
        ("services/lighthouse/configs/config_desktop.json", "services/lighthouse/configs/config_desktop.json"),
        ("services/lighthouse/configs/config_mobile.json", "services/lighthouse/configs/config_mobile.json"),

        # Creds
        ("services/lighthouse/creds/voluptas-488008-e88abce2f685.json",
         "services/lighthouse/configs/creds/service_account.json"),
    ]

    for src_rel, dst_rel in copies:
        src = PROJECT_ROOT / src_rel
        dst = PACKAGE_DIR / dst_rel

        if not src.exists():
            # Создаём пустой __init__.py если исходный не существует
            if src.name == "__init__.py":
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("")
                continue
            else:
                print(f"[WARNING] Файл не найден: {src}")
                continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  Копирую: {src_rel} -> {dst_rel}")


def patch_pagespeed_service():
    """Убирает pytest-декоратор и импорт из pagespeed_service.py."""
    filepath = PACKAGE_DIR / "services" / "lighthouse" / "pagespeed_service.py"
    if not filepath.exists():
        print("[WARNING] pagespeed_service.py не найден для патча")
        return

    content = filepath.read_text(encoding="utf-8")

    # Убираем import pytest
    content = re.sub(r'^import pytest\s*\n', '', content, flags=re.MULTILINE)

    # Убираем @pytest.mark.skip(...)
    content = re.sub(r'^@pytest\.mark\.skip\(.*?\)\s*\n', '', content, flags=re.MULTILINE)

    filepath.write_text(content, encoding="utf-8")
    print("  Патч: убран pytest из pagespeed_service.py")


def patch_env_creds_path():
    """Обновляет путь к creds в .env — используем относительный путь внутри пакета."""
    env_path = PACKAGE_DIR / "services" / "lighthouse" / "configs" / "config_lighthouse.env"
    if not env_path.exists():
        return

    content = env_path.read_text(encoding="utf-8")

    # Меняем путь GS_CREDS на путь внутри standalone-пакета
    content = re.sub(
        r'^GS_CREDS=.*$',
        'GS_CREDS=services/lighthouse/configs/creds/service_account.json',
        content,
        flags=re.MULTILINE,
    )

    env_path.write_text(content, encoding="utf-8")
    print("  Патч: обновлён путь GS_CREDS в .env")


def create_zip():
    """Создаёт zip-архив пакета."""
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PACKAGE_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = "lighthouse_runner" / file_path.relative_to(PACKAGE_DIR)
                zf.write(file_path, arcname)

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\n  Архив создан: {ZIP_PATH} ({size_mb:.2f} MB)")


def main():
    print("=" * 50)
    print("  Сборка Standalone Lighthouse Runner")
    print("=" * 50)

    print("\n[1/5] Очистка предыдущей сборки...")
    clean_output()

    print("\n[2/5] Копирование файлов...")
    copy_files()

    print("\n[3/5] Патч pagespeed_service.py...")
    patch_pagespeed_service()

    print("\n[4/5] Патч .env (путь к creds)...")
    patch_env_creds_path()

    print("\n[5/5] Создание zip-архива...")
    create_zip()

    print("\n" + "=" * 50)
    print("  Готово!")
    print(f"  Пакет: {PACKAGE_DIR}")
    print(f"  Архив: {ZIP_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
