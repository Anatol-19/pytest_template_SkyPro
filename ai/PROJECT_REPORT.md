# Отчёт по проекту pytest_template_SkyPro

> Дата индексации: 2026-06-09  
> Назначение: справочный документ для ИИ-агентов и разработчиков о структуре, архитектуре и состоянии проекта.

---

## Назначение проекта

QA-фреймворк для автоматизированного тестирования платформ **VRPorn** (`vrporn.com`) и **VRSmash** (`vrsmash.com`). Три независимых направления:

| Направление | Файлы тестов | Инструменты |
|---|---|---|
| Функциональные / GUI | `test/simple_test.py` | Pytest + Selenium |
| Производительность | `test/speed_test.py` | Pytest + Lighthouse CLI / PageSpeed API |
| Content Assets (API) | `test/test_content_assets.py` | Pytest + Requests |
| Payment (API) | `test/test_payment.py` | Pytest + Requests |

---

## Архитектурная карта

```
pytest_template_SkyPro/
│
├── test/                        # Тесты
│   ├── conftest.py              # Фикстуры, CLI-опции
│   ├── simple_test.py           # GUI-тесты (Selenium)
│   ├── speed_test.py            # Perf-тесты (Lighthouse)
│   ├── test_content_assets.py   # API-тесты (Content Assets)
│   └── test_zoho.py             # ОТКЛЮЧЁН в pytest.ini
│
├── POM/                         # Page Object Model
│   ├── AuthPage.py
│   └── selectors.py
│
├── helper/                      # Вспомогательные классы для UI
│   ├── StartSession.py          # Управление WebDriver
│   ├── GUIHelper.py             # Обёртки над элементами
│   └── user_agents.py
│
├── REST/                        # REST-клиент
│   ├── base_client.py           # BaseApiClient — ядро HTTP-слоя
│   └── auth_client.py           # AuthClient — логин мембера
│
├── URLs/
│   ├── base_urls.ini            # URL по окружениям (VRS/VRP × DEV/TEST/STAGE/PROD)
│   ├── routes.ini               # Именованные маршруты
│   └── routes.py                # (legacy dict, не используется BaseApiClient)
│
├── services/
│   ├── lighthouse/              # Сервис перф-тестирования
│   │   ├── pagespeed_service.py # SpeedtestService — оркестратор
│   │   ├── cli_runner.py        # Запуск Lighthouse CLI
│   │   ├── api_runner.py        # Google PageSpeed Insights API
│   │   ├── processor_lighthouse.py  # Парсинг + агрегация метрик
│   │   ├── mcp_server.py        # FastMCP сервер для Claude
│   │   ├── run.py               # Точка входа CLI
│   │   ├── configs/
│   │   │   ├── config_lighthouse.py   # Пути, хелперы, кэш BASE_URL
│   │   │   ├── config_lighthouse.env  # API-ключи, Sheet IDs (gitignored)
│   │   │   ├── config_desktop.json    # Lighthouse desktop config
│   │   │   └── config_mobile.json     # Lighthouse mobile config
│   │   └── Google Sheet/        # Apps Script для дашборда
│   │
│   ├── google/
│   │   └── google_sheets_client.py  # Запись результатов в Google Sheets
│   │
│   ├── content_assets/          # Верификация CDN-ассетов
│   │   ├── verifier.py          # ContentAssetVerifier — главный класс
│   │   ├── content_client.py    # Запросы к content API
│   │   ├── csv_loader.py        # Загрузка CSV с ожидаемыми путями
│   │   ├── asset_mapper.py      # Маппинг ответа API → ActualAsset
│   │   ├── signed_url_validator.py  # Проверка ttl/token, HEAD CDN
│   │   ├── report_writer.py     # Запись CSV-отчётов
│   │   └── models.py            # Датаклассы: ExpectedAsset, VerificationResult
│   │
│   ├── payment/                 # Платёжный флоу VRP (Layer 01-03)
│   │   ├── payment_flow.py       # PaymentFlow — оркестратор сценариев
│   │   ├── payment_client.py     # PaymentClient(BaseApiClient) + парсеры + self_host
│   │   ├── epoch_payloads.py     # билдеры тел FlexPost/DataPlus/Cancel/FlexGrade
│   │   ├── models.py             # TariffPrice, PaymentResult, PaymentSession
│   │   ├── fakes.py              # fake-данные, inc_tx, money
│   │   ├── config_payment.py     # константы Epoch sandbox + контуры
│   │   └── README.md
│   │
│   ├── ZOHO/                    # Zoho Projects API (тесты отключены)
│   │   ├── Zoho_api_client.py
│   │   ├── User.py, TaskStatus.py, DefectStatus.py
│   │   ├── portal_data.py
│   │   └── config_zoho.env      # (gitignored)
│   │
│   └── Release_Test_Plan/
│       └── TestPlanGenerator.py # Генерация QA тест-планов из Zoho
│
├── tools/clasp/                 # Apps Script миррор для clasp
├── config.py                    # Глобальные переменные (инициализируются conftest)
├── config.ini                   # ui_url, ui_auth_url
├── pytest.ini                   # testpaths, markers, ignore test_zoho
├── requirements.txt
└── CLAUDE.md                    # Инструкции для Claude Code
```

---

## Ключевые потоки данных

### Перф-тест (Lighthouse)
```
speed_test.py
  └── SpeedtestService(environment=...)
        ├── cli_runner → Lighthouse CLI → JSON-отчёт
        ├── api_runner → PageSpeed API → JSON-ответ
        ├── processor_lighthouse → агрегация метрик (avg/p90/min/max)
        └── GoogleSheetsClient.flush() → запись строк в таблицу
```

### Content Assets
```
test_content_assets.py
  └── ContentAssetVerifier(environment=..., check_http=...)
        ├── AuthClient.login() → POST /proxy-user/api/wp/auth/login → atoken
        ├── ContentClient.get_post(slug) → GET /proxy/api/content/v1/post/{slug}
        ├── asset_mapper → ActualAsset[]
        ├── signed_url_validator → ttl, token_present
        └── report_writer → _asset_report.csv + _verified.csv
```

### GUI-тест
```
simple_test.py
  └── browser fixture (conftest)
        └── webdriver.Chrome(ChromeDriverManager)
              └── AuthPage.login() → Selenium actions
```

---

## Окружения

| Секция | Продукт | Уровень |
|---|---|---|
| VRS_DEV / VRS_TEST / VRS_STAGE / VRS_PROD | VRSmash | dev→prod |
| VRP_DEV / VRP_TEST / VRP_STAGE / VRP_PROD | VRPorn | dev→prod |

Активное окружение: `URLs/base_urls.ini → [environments] current` (по умолчанию `VRP_PROD`).  
Для `SpeedtestService` и `BaseApiClient` окружение передаётся параметром конструктора — `base_urls.ini` не мутируется.

---

## Переменные окружения / секреты

| Файл | Что хранит |
|---|---|
| `.env` (корень) | `VRP_MEMBER_EMAIL`, `VRP_MEMBER_PASSWORD` |
| `services/lighthouse/configs/config_lighthouse.env` | `PAGESPEED_API_KEY`, Google Sheets ID, worksheet names |
| `services/ZOHO/config_zoho.env` | Zoho API токены |
| `services/lighthouse/creds/*.json` | Google service account для Sheets |

Все файлы из этого списка добавлены в `.gitignore`.

---

## Метрики Lighthouse

`P` (Performance score), `LCP`, `FCP`, `TBT`, `CLS`, `SI`, `TTI`, `TTFB`, `INP`.  
CrUX данные доступны только для `*_PROD` окружений.  
Типы устройств: `"desktop"` / `"mobile"` (соответствуют именам JSON-конфигов).

---

## Статус компонентов

| Компонент | Статус |
|---|---|
| GUI тесты (Selenium) | Рабочий, Chrome/Firefox |
| Lighthouse CLI runner | Рабочий |
| PageSpeed API runner | Рабочий, rate limiter встроен |
| Google Sheets client | Рабочий |
| MCP сервер | Рабочий, FastMCP, async job queue |
| Content Assets verifier | Рабочий |
| REST BaseApiClient | Рабочий |
| ZOHO сервис | В разработке, тесты отключены |
| TestPlanGenerator | В разработке |
| Opera / Edge WebDriver | Закомментированы (TODO) |

---

## Известные ограничения и TODO

- `test_zoho.py` исключён через `pytest.ini` (`--ignore=test/test_zoho.py`)
- Opera и Edge WebDriver закомментированы в `helper/StartSession.py`
- `URLs/routes.py` — legacy dict, не используется `BaseApiClient` (тот читает `routes.ini`)
- `config.ini` содержит `ui_url` / `ui_auth_url` для Strive (отдельный продукт)
- JMeter план (`services/JMetr/`) включён в репозиторий, но не интегрирован с Pytest
