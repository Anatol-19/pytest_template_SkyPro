#!/usr/bin/env bash
# Генерация Allure-отчёта с сохранением истории и тренда между прогонами.
#
# Тренд в Allure строится из папки history: её нужно переносить из предыдущего
# отчёта в свежие результаты ПЕРЕД генерацией. Этот скрипт делает это автоматически.
#
# Использование:
#   bash tools/allure_report.sh          # сгенерировать и открыть отчёт
#   bash tools/allure_report.sh --serve   # быстрый просмотр без сохранения истории
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESULTS="$ROOT/Reports/allure"
REPORT="$ROOT/Reports/allure-report"

if ! command -v allure >/dev/null 2>&1; then
  echo "Allure CLI не найден. Установите: brew install allure" >&2
  exit 1
fi

if [ "${1:-}" = "--serve" ]; then
  allure serve "$RESULTS"
  exit 0
fi

# 1. перенести историю из предыдущего отчёта в свежие результаты (для тренда)
if [ -d "$REPORT/history" ]; then
  cp -r "$REPORT/history" "$RESULTS/history"
  echo "История перенесена из предыдущего отчёта."
fi

# 2. сгенерировать статический отчёт (--clean чистит только папку отчёта, не результаты)
allure generate "$RESULTS" -o "$REPORT" --clean

# 3. открыть в браузере
allure open "$REPORT"
