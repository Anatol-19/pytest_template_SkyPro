# Payment tests — платёжный флоу VRP

API-тесты платёжного флоу VRPorn (Join / Upgrade / Cancel / Refund / Rebill).
Все Epoch-операции идут через бэкенд-прокси `/api/payment/sync-handler/epoch`
(прямых вызовов `bs.epoch.com` нет). Транзакции отправляются с `isTest=true`.

Детали API: `ai/POSTMAN_ANALYSIS.md`. ТЗ: `ai/VRP_PAYMENT_TESTING.md`.

## Контуры

Контур задаётся `--environment` (секция из `URLs/base_urls.ini`):

| Контур | Секция | host |
|---|---|---|
| Dev | `VRP_DEV` | `d.vrporn.com` |
| Test | `VRP_TEST` | `t.vrporn.com` |
| Stage | `VRP_STAGE` (default) | `sg.vrporn.com` |
| Prod | `VRP_PROD` | `vrporn.com` |

Весь код контур-агностичен. PROD из дефолтного мульти-прогона исключён.

## ENV

`.env` в корне проекта (учётка существующего мембера для Layer 03 / re-join):

```env
VRP_PAY_EMAIL=...
VRP_PAY_PASSWORD=...
```

Layer 01 (тарифы) и большинство join-сценариев учётку не требуют.

## Запуск

```bash
# Всё на STAGE
pytest -m payment --environment=VRP_STAGE -v

# Только тарифы (smoke, без транзакций)
pytest test/test_payment.py::TestTariffs --environment=VRP_DEV -v

# Конкретная категория/таб
pytest -m payment --environment=VRP_STAGE --pay-category=bundle --pay-tab=monthly

# Несколько контуров подряд
python run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE
```

### Управление выбором тарифа

| Флаг | Что выбирает |
|---|---|
| `--pay-tab` | Период покупки: `monthly` \| `yearly` \| `lifetime` (алиасы `year`/`month`/`life`). По умолчанию `monthly`. Если значение не сматчилось — тест падает с явной ошибкой (никогда не берётся «первый молча»). |
| `--pay-slot` | Standard vs Special цены внутри прайс-группы. Пусто = Standard; `N` (напр. `2`) = Special — отдельный запрос `?type_prices_from_slot=N&event_id=<uuid>&event=`, `event_id` берётся из текущего Sale Event. |

```bash
pytest -m payment --environment=VRP_TEST --pay-tab=yearly
pytest -m payment --environment=VRP_TEST --pay-tab=lifetime
pytest -m payment --environment=VRP_TEST --pay-tab=monthly --pay-slot=2   # special
```

Прайс на уровне API:
```
Standard:  GET /proxy-user/api/memberships/prices
Special:   GET /proxy-user/api/memberships/prices?type_prices_from_slot=2&event_id=<uuid>&event=
```

Категория (ключ `prices[...]`) задаётся бэкендом — тест берёт первую доступную.

> Sale event как **механизм выбора прайс-группы** не реализован (используем текущий sale
> event только чтобы взять `event_id` для спец-цен). Это отдельная задача.

Полезное: `-k standard` (фильтр по имени), `-s` (показать print), `-v` (подробно).

## Allure-отчёты

Allure включён **по умолчанию** (`--alluredir=Reports/allure` в `pytest.ini`), результаты
**накапливаются** между прогонами. Отключить разово: флаг `--no-allure`.

```bash
# 1. установить Allure CLI (однократно)
brew install allure

# 2. прогнать тесты (результаты копятся в Reports/allure)
pytest test/test_payment.py::TestJoins --environment=VRP_TEST -v

# 3. сгенерировать отчёт с историей и трендом + открыть
bash tools/allure_report.sh

# быстрый просмотр без сохранения истории
bash tools/allure_report.sh --serve
```

**Тренд/история.** Вкладка Trend в Allure строится из папки `history`, которую нужно
переносить между генерациями. `tools/allure_report.sh` делает это сам: копирует
`Reports/allure-report/history` в свежие результаты перед генерацией. Поэтому для
накопления тренда генерируйте отчёт этим скриптом после каждого прогона.

К каждому payment-тесту автоматически прикладывается **сводка сессии** (email, member_id,
membership_uuid, invoice_uuid, статус, tx) — в Allure-вложение «Payment session» и в лог,
для сверки на фронте и в админке.

Артефакты (`Reports/`) в `.gitignore`.

## Структура

| Файл | Назначение |
|---|---|
| `models.py` | `TariffPrice`, `PaymentResult`, `PaymentSession` |
| `fakes.py` | генераторы fake-данных, `inc_tx`, `money` |
| `config_payment.py` | константы Epoch sandbox + маппинг контуров |
| `payment_client.py` | `PaymentClient(BaseApiClient)` — HTTP + парсеры |
| `epoch_payloads.py` | билдеры тел FlexPost/DataPlus/Cancel/FlexGrade |
| `payment_flow.py` | `PaymentFlow` — оркестратор сценариев |

## Сценарии

- **Layer 01** — Sale Event, Prices (smoke).
- **Layer 02** — Standard / Free Trial / Paid Trial / Lifetime / Re-join + Rebill.
- **Layer 03** — Upgrade (Flexgrade), Easy Cancel Downgrade, Refund.
