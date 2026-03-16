
# Lighthouse Automation Service

Сервис для автоматизированного тестирования производительности веб-страниц через Lighthouse CLI и сбора CrUX-метрик.

## Быстрый старт

### 1. Выбрать контур

В файле `URLs/base_urls.ini` указать нужный контур:
```ini
[environments]
current = VRP_DEV
```

Доступные контуры:
| Контур | URL |
|--------|----|
| `VRS_DEV` | https://dev.vrsmash.com |
| `VRS_TEST` | https://test.vrsmash.com |
| `VRS_STAGE` | https://stage.vrsmash.com |
| `VRS_PROD` | https://www.vrsmash.com |
| `VRP_DEV` | https://d.vrporn.com |
| `VRP_TEST` | https://t.vrporn.com |
| `VRP_STAGE` | https://sg.vrporn.com |
| `VRP_PROD` | https://vrporn.com |

### 2. Указать роуты

В файле `URLs/routes.ini`:
```ini
[routes]
home = /
login = /login
```

### 3. Запустить тест

```python
from dotenv import load_dotenv
load_dotenv('services/lighthouse/configs/config_lighthouse.env', override=True)

import services.lighthouse.configs.config_lighthouse as cfg
cfg.BASE_URL = None  # сброс кэша при смене контура

from services.lighthouse.pagespeed_service import SpeedtestService

service = SpeedtestService()

# CLI: 10 прогонов, агрегация (min/max/avg/p90) -> Google Sheets
service.run_local_tests(['home'], 'desktop', n_iteration=10)

# CrUX: реальные пользовательские метрики (только PROD)
service.run_crux_data_collection(['home'], 'desktop')
```

**Параметры `run_local_tests`:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `route_keys` | `list[str]` | все из routes.ini | Ключи роутов |
| `device_type` | `str` | — | `"desktop"` или `"mobile"` |
| `n_iteration` | `int` | `10` | Количество прогонов |
| `keep_temp_files` | `bool` | `False` | Сохранять JSON-отчёты |
| `base_url` | `str` | из конфига | Переопределить URL |

## Структура проекта

```
services/lighthouse/
  pagespeed_service.py       # Оркестратор запусков
  cli_runner.py              # Запуск Lighthouse CLI
  api_runner.py              # Google PageSpeed API
  processor_lighthouse.py    # Парсинг, агрегация, запись в Sheets
  configs/
    config_lighthouse.py     # Пути, роуты, окружения
    config_lighthouse.env    # API-ключи, ID таблицы, credentials
    config_desktop.json      # Эмуляция desktop (1350x940)
    config_mobile.json       # Эмуляция mobile (375x667)
  creds/
    *.json                   # Ключ сервисного аккаунта Google

URLs/
  base_urls.ini              # Контуры (проект + среда)
  routes.ini                 # Роуты для тестирования

Reports/reports_lighthouse/
  temp_lighthouse/           # Временные JSON-отчёты (удаляются после агрегации)
```

## Google Sheets

Результаты пишутся в Google Таблицу. Листы создаются автоматически.

**Листы CLI** (по одному на контур):
`VRS [DEV] CLI`, `VRS [TEST] CLI`, `VRS [STAGE] CLI`, `VRS [PROD] CLI`,
`VRP [DEV] CLI`, `VRP [TEST] CLI`, `VRP [STAGE] CLI`, `VRP [PROD] CLI`

**Лист CrUX**: `CrUX` (общий для обоих проектов)

### Запись данных

Данные пишутся **по имени заголовка**: скрипт читает заголовки из первой строки листа, находит нужный столбец по названию и записывает значение в соответствующую позицию. Порядок столбцов в таблице можно менять — запись не сломается.

### Метрики CLI (агрегированные за N прогонов)

Каждая метрика записывается в 4 столбца: `min`, `max`, `avg`, `p90`

| Метрика | Описание | Good | Needs Improvement | Poor |
|---------|----------|------|-------------------|------|
| P | Performance score (0-100) | >= 90 | 50-89 | < 50 |
| LCP | Largest Contentful Paint, мс | <= 2500 | 2500-4000 | > 4000 |
| FCP | First Contentful Paint, мс | <= 1800 | 1800-3000 | > 3000 |
| TBT | Total Blocking Time, мс | <= 200 | 200-600 | > 600 |
| CLS | Cumulative Layout Shift | <= 0.1 | 0.1-0.25 | > 0.25 |
| SI | Speed Index, мс | <= 3400 | 3400-5800 | > 5800 |
| TTI | Time to Interactive, мс | <= 3800 | 3800-7300 | > 7300 |
| TTFB | Time to First Byte, мс | <= 800 | 800-1800 | > 1800 |
| INP | Interaction to Next Paint, мс | <= 200 | 200-500 | > 500 |

## Настройка Google Sheets (с нуля)

1. Создать Google Cloud проект, включить Google Sheets API
2. Создать Service Account, скачать JSON-ключ
3. Положить ключ в `services/lighthouse/creds/`
4. Создать Google Таблицу, расшарить на email сервисного аккаунта (редактор)
5. Вписать в `config_lighthouse.env`:
   ```
   GS_CREDS=services/lighthouse/creds/your-key.json
   GS_SHEET_ID=ID_таблицы_из_URL
   ```

## Требования

- Python 3.10+
- Node.js + npm
- Lighthouse CLI: `npm install -g lighthouse`
- Python-пакеты: `gspread`, `google-auth`, `numpy`, `python-dotenv`, `requests`
