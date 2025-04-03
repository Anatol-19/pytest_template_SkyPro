import subprocess
import shutil

# Определяем путь к команде Lighthouse
LIGHTHOUSE_CMD = shutil.which("lighthouse")

if LIGHTHOUSE_CMD is None:
    raise RuntimeError("Lighthouse не найден в системном пути. Установите его командой: npm install -g lighthouse")

def run_lighthouse(url: str, mode: str, output_dir: str) -> str:
    """
    Запускает Lighthouse для указанного URL и сохраняет отчет в указанную директорию.
    :param url: URL страницы, для которой нужно запустить Lighthouse.
    :param mode: Режим запуска (mobile или desktop).
    :param output_dir: Путь к файлу, в который будет сохранен отчет.
    :return: Путь к файлу с отчетом.
    :raises RuntimeError: Если команда Lighthouse завершилась с ошибкой.
    """
    command = [
        LIGHTHOUSE_CMD, url,
        "--output=json",
        f"--output-path={output_dir}",
        "--chrome-flags=--headless --no-sandbox"
    ]

    if mode == "mobile":
        command.append("--preset=mobile")
    else:
        command.append("--preset=desktop")

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при запуске Lighthouse: {result.stderr}")

    return output_dir
