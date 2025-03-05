import subprocess
import os
import json


def run_lighthouse(url: str, mode: str, output_dir: str) -> str:
    """Запускает Lighthouse CLI и сохраняет результаты в JSON."""

    if mode not in ["desktop", "mobile"]:
        raise ValueError("Режим должен быть 'desktop' или 'mobile'")

    output_file = os.path.join(output_dir, f"lighthouse_{mode}.json")

    # Формируем команду для Lighthouse
    command = [
        "lighthouse", url,
        "--output=json",
        f"--output-path={output_file}",
        "--chrome-flags=--headless"
    ]

    if mode == "mobile":
        command.append("--preset=mobile")
    else:
        command.append("--preset=desktop")

    # Запускаем Lighthouse
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при запуске Lighthouse: {result.stderr}")

    return output_file
