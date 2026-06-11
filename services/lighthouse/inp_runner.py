"""
Модуль для измерения INP через Lighthouse timespan mode.
Запускает Node.js скрипт, который:
1. Загружает страницу (navigation)
2. Находит первый интерактивный элемент
3. Кликает по нему (timespan)
4. Измеряет INP
"""

import json
import os
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path


def run_inp_test(
    url: str,
    device: str = "desktop",
    output_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Запускает INP тест через Lighthouse timespan mode.
    
    Args:
        url: URL для тестирования
        device: Тип устройства (desktop/mobile)
        output_dir: Директория для сохранения результатов
        
    Returns:
        Dict с результатами или None при ошибке
    """
    # Путь к Node.js скрипту
    script_dir = Path(__file__).parent.parent.parent / "scripts"
    inp_script = script_dir / "lighthouse_inp.js"
    
    if not inp_script.exists():
        print(f"[ERROR] INP script not found: {inp_script}")
        return None
    
    # Директория для результатов
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "temp_reports" / "inp"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Запуск Node.js скрипта
    try:
        result = subprocess.run(
            ["node", str(inp_script), url, device, str(output_dir)],
            capture_output=True,
            text=True,
            timeout=120  # 2 минуты максимум
        )
        
        if result.returncode != 0:
            print(f"[ERROR] INP test failed: {result.stderr}")
            return None
        
        # Парсим результат (последняя строка - JSON)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if 'inp' in data:
                    return data
            except json.JSONDecodeError:
                continue
        
        print(f"[WARN] Could not parse INP result from: {result.stdout}")
        return None
        
    except subprocess.TimeoutExpired:
        print(f"[ERROR] INP test timeout for {url}")
        return None
    except Exception as e:
        print(f"[ERROR] INP test error: {e}")
        return None


def parse_inp_result(json_file: str) -> Optional[Dict[str, Any]]:
    """
    Парсит результат INP теста из JSON файла.
    
    Args:
        json_file: Путь к JSON файлу
        
    Returns:
        Dict с INP метрикой или None
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "INP": data.get("inp", None),
            "url": data.get("url"),
            "device": data.get("device"),
            "timestamp": data.get("timestamp")
        }
    except Exception as e:
        print(f"[ERROR] Error parsing INP result: {e}")
        return None


def aggregate_inp_results(results: list) -> Dict[str, float]:
    """
    Агрегирует результаты INP тестов.
    
    Args:
        results: Список результатов INP тестов
        
    Returns:
        Dict с avg, p75, p90 для INP
    """
    import numpy as np
    
    inp_values = [r.get("INP") for r in results if r and r.get("INP") is not None]
    
    if not inp_values:
        return {"INP_avg": None, "INP_p75": None, "INP_p90": None}
    
    return {
        "INP_avg": round(np.mean(inp_values), 2),
        "INP_p75": round(np.percentile(inp_values, 75), 2),
        "INP_p90": round(np.percentile(inp_values, 90), 2)
    }