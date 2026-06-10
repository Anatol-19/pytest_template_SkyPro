# Передача контекста для ИИ-агента

> Этот документ — точка входа для нового ИИ-агента (или новой сессии Claude Code).  
> Прочитай его первым, затем при необходимости открывай файлы из списка ниже.

---

## Что это за проект

QA-фреймворк автоматизации для платформ **VRPorn** и **VRSmash**.  
Язык: Python 3.12. Фреймворк тестирования: Pytest.  
Все комментарии, docstrings и сообщения в логах — на **русском языке**.

---

## Минимальный контекст для старта

### Чтобы запустить тесты:
```bash
# Установить зависимости
pip install -r requirements.txt

# GUI-тесты
pytest -m functional

# Перф-тесты
pytest -m performance

# Content Assets
pytest test/test_content_assets.py --environment=VRP_PROD --assets-csv="/path/to/file.csv"
```

### Чтобы добавить новый тест:
1. **GUI**: добавь метод в `POM/` (Page Object), используй `helper/GUIHelper.py` для взаимодействия с элементами, создай тест в `test/simple_test.py` с маркером `@pytest.mark.functional`.
2. **API**: используй `REST/base_client.py` → `BaseApiClient`, добавь маршрут в `URLs/routes.ini`.
3. **Перф**: добавь маршрут в `URLs/routes.ini`, вызови `SpeedtestService` из `services/lighthouse/pagespeed_service.py`.

### Чтобы добавить новый маршрут:
Открой `URLs/routes.ini`, добавь строку в секцию `[routes]`:
```ini
my_page = /path/to/page/
```

### Чтобы переключить окружение:
- Для `BaseApiClient` / content tests: `--environment=VRP_STAGE` или `BaseApiClient(environment="VRP_STAGE")`
- Для Lighthouse: `SpeedtestService(environment="VRP_STAGE")`
- **Не редактируй** `[environments] current` в `base_urls.ini` — это сломает параллельные запуски.

---

## Критически важные файлы

| Файл | Зачем читать |
|---|---|
| `CLAUDE.md` | Полная инструкция для Claude Code |
| `ai/PROJECT_REPORT.md` | Полный отчёт по архитектуре проекта |
| `URLs/base_urls.ini` | Все окружения и их URL |
| `URLs/routes.ini` | Все именованные маршруты |
| `REST/base_client.py` | Ядро HTTP-клиента |
| `test/conftest.py` | Все фикстуры и CLI-флаги |
| `services/lighthouse/pagespeed_service.py` | Оркестратор Lighthouse |
| `services/content_assets/verifier.py` | Логика верификации CDN |

---

## Переменные окружения (нужны для запуска)

Создай `.env` в корне проекта:
```env
VRP_MEMBER_EMAIL=...
VRP_MEMBER_PASSWORD=...
```

Для Lighthouse создай `services/lighthouse/configs/config_lighthouse.env`:
```env
PAGESPEED_API_KEY=...
SPREADSHEET_ID=...
# и другие — см. config_lighthouse.py
```

---

## Что сейчас не работает / отключено

- `test/test_zoho.py` — исключён в `pytest.ini`, ZOHO-сервис в разработке
- Opera и Edge WebDriver — закомментированы в `helper/StartSession.py`
- `services/JMetr/` — JMeter план есть, но не интегрирован с Pytest

---

## Типичные задачи и с чего начать

| Задача | Стартовый файл |
|---|---|
| Добавить GUI-тест | `POM/AuthPage.py` → `test/simple_test.py` |
| Добавить API-проверку | `REST/base_client.py` → новый `_client.py` в `services/` |
| Добавить перф-маршрут | `URLs/routes.ini` → `test/speed_test.py` |
| Отладить content assets | `services/content_assets/verifier.py` |
| Добавить инструмент в MCP | `services/lighthouse/mcp_server.py` |
| Обновить дашборд Google Sheets | `services/lighthouse/Google Sheet/*.gs` + `tools/clasp/` |

---

## Соглашения кодовой базы

- Все сообщения, логи, комментарии — **по-русски**
- `BaseApiClient` читает маршруты из `routes.ini`, не из `routes.py` (legacy)
- ConfigParser возвращает ключи в нижнем регистре: `base_url`, не `BASE_URL`
- Метрики Lighthouse: `P`, `LCP`, `FCP`, `TBT`, `CLS`, `SI`, `TTI`, `TTFB`, `INP`
- Типы устройств: строго `"desktop"` или `"mobile"`
- Отчёты: `Reports/reports_lighthouse/`, временные файлы: `Reports/reports_lighthouse/temp_lighthouse/`
