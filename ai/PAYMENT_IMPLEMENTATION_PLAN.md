# План реализации: Payment Testing

> Дата: 2026-06-10  
> Scope: полное покрытие Layer 01–03  
> Подход: реализация по реальной Postman-коллекции (см. `POSTMAN_ANALYSIS.md`), тест-данные тянутся динамически из API.  
> Принцип: **не нарушать структуру фреймворка** — наследуемся от `BaseApiClient`, маршруты в `routes.ini`, модели-датаклассы, комментарии на русском.

---

## Фаза 0 — Переписать ТЗ

Файл `ai/VRP_PAYMENT_TESTING.md` содержит ошибки (прямые вызовы `bs.epoch.com`, неверные URL, неверная структура ответов).

**Действие:** переписать его на основе `POSTMAN_ANALYSIS.md`:
- Убрать `EpochClient` к `bs.epoch.com` — всё идёт через прокси `/api/payment/sync-handler/epoch`.
- Исправить все URL (таблица в анализе).
- Исправить структуру `/prices` (dict по категориям) и Sale Event.
- Описать реальные тела FlexPost (JSON) и DataPlus (form, `ets_`).
- Зафиксировать цепочки всех сценариев Layer 01–03.

---

## Фаза 1 — Конфигурация

### 1.1 `URLs/routes.ini` — добавить секцию payment

```ini
; --- Payment / Join ---
join_sale_event         = /proxy-user/api/memberships/join-now/user-sale-event
join_prices             = /proxy-user/api/memberships/prices
payment_url_new         = /api/memberships/join-now/get-recurring-payment-url
payment_url_exist       = /api/memberships/join-now/get-recurring-payment-url-exist
epoch_sync              = /api/payment/sync-handler/epoch
invoice_status          = /api/payment/invoice/status
auth_payment            = /api/wp/secure/auth/login
dashboard_info          = /proxy-user/api/wp/user/dashboardInfo
upgrade_rules           = /proxy-user/api/memberships/service/price-upgrade-rules
upgrade_url_epoch       = /proxy-user/api/payment/recurring-upgrade-url/epoch
easy_cancel_upgrade_url = /proxy-user/api/easy-cancel/upgrade-url
```

### 1.2 `base_urls.ini` — все 4 VRP-контура
Коллекция полностью параметризована через `{{Base_url}}` — контур = значение переменной. Отдельные `JOIN`-секции **не нужны** (ошибка ТЗ). Используем уже существующие секции:

| Контур | Секция | host (`base_url`) |
|---|---|---|
| Dev | `VRP_DEV` | `d.vrporn.com` |
| Test | `VRP_TEST` | `t.vrporn.com` |
| Stage | `VRP_STAGE` | `sg.vrporn.com` |
| Prod | `VRP_PROD` | `vrporn.com` |

Ничего добавлять в `base_urls.ini` не требуется — все четыре контура уже описаны.

### 1.3 `pytest.ini` — новый маркер
```ini
markers =
    functional: Тесты функциональных кейсов
    performance: Тесты на производительность
    payment: Тесты платёжного флоу (Join, Upgrade, Cancel, Refund, Rebill)
```

### 1.4 `.env` — новые переменные
```dotenv
# Payment — тестовая учётка мембера для Layer 03 / re-join
VRP_PAY_EMAIL=...
VRP_PAY_PASSWORD=...
```
> Секреты вроде `epoch_digest` уже хардкод-константа в коллекции (`b1bd...._qa`) — выносим в config-модуль, не в .env.

---

## Фаза 1.5 — Мульти-контур (DEV / TEST / STAGE / PROD)

Все методы и сценарии **контур-агностичны**: контур задаётся один раз при создании `PaymentClient(environment=...)`, дальше `BaseApiClient` сам резолвит `base_url`. Тот же тест-код гоняется на любом из 4 VRP-контуров.

### Что нужно учесть

1. **Self-host резолвинг.** Единственное место в коллекции с захардкоженным хостом — проверка self-separated бандла (`host === 'vrporn.com' || 'sg.vrporn.com'`). Реализуем динамически:
   ```python
   from urllib.parse import urlparse
   self_host = urlparse(self.base_url).netloc   # d.vrporn.com / t.vrporn.com / sg.vrporn.com / vrporn.com
   # self-separated, если bundled-хост совпадает с self_host (или с голым 'vrporn.com')
   ```
2. **Выбор контура** — через существующий флаг `--environment` (default `VRP_STAGE`). Один прогон = один контур.
3. **Прогон по всем контурам** — два варианта (реализуем оба, см. фазы 6 и 7):
   - повтор `pytest -m payment --environment=VRP_DEV|VRP_TEST|VRP_STAGE`;
   - root-скрипт `run_payment_contours.py` (по образцу существующих `run_*.py`), последовательно гоняющий выбранные контуры.
4. **Защита PROD** — `VRP_PROD` исключён из дефолтного мульти-прогона; запуск на нём только явным `--environment=VRP_PROD`. Все транзакции идут с `isTest=true`.
5. **UnZip (`api-stag.unzipvr.com`)** — внешний staging-only сервис из `_Utils`, в основной флоу **не входит**, в scope не берём.

---

## Фаза 2 — Структура сервиса

```
services/payment/
├── __init__.py
├── models.py            # датаклассы
├── fakes.py             # генераторы fake-данных + inc_tx
├── config_payment.py    # константы (zip, ipaddr, co_code, epoch_digest, invoiceProduct map)
├── payment_client.py    # PaymentClient(BaseApiClient) — HTTP-слой
├── epoch_payloads.py    # сборка тел FlexPost (JSON) и DataPlus/Cancel (form)
├── payment_flow.py      # PaymentFlow — оркестратор сценариев
└── README.md
```

### 2.1 `models.py`
```python
@dataclass
class TariffPrice:
    membership_id: str        # = subscr_id / price_uuid
    epoch_pi_code: str
    amount: str               # money(trial_price ?? price ?? rebill_price)
    currency: str = "USD"
    category: str = "standard"
    tab: str = "monthly"
    raw: dict = field(default_factory=dict)

@dataclass
class PaymentResult:
    payment_url: str
    invoice_uuid: str
    user_uuid: str
    is_dynamic_url: bool = False

@dataclass
class PaymentSession:
    """Накапливает состояние по ходу флоу."""
    email: str
    password: str
    price: TariffPrice = None
    invoice_uuid: str = ""
    user_uuid: str = ""
    member_id: str = ""
    transaction_id: str = ""
    initial_transaction_id: str = ""
    last_dataplus_id: str = ""
    atoken: str = ""
    membership_uuid: str = ""
    member_status: str = ""
    active_pi_code: str = ""
    active_amount: str = ""
    active_currency: str = "USD"
    is_bundle: bool = False
    bundle_slave_picodes: dict = field(default_factory=dict)
```

### 2.2 `fakes.py`
Портируем JS-хелперы из pre-scripts:
```python
def fake_member_id() -> str        # '4219' + 9 цифр
def fake_transaction_id() -> str   # '108qa' + 6 цифр
def fake_session_id() -> str       # 32 цифры + '_qa'
def epoch_time() -> str            # unix timestamp
def transaction_date() -> str      # 'YYYY-MM-DD HH:MM:SS'
def inc_tx(tx_id, step=3) -> str   # инкремент числового хвоста
def money(v) -> str                # f"{float:.2f}"
```

### 2.3 `config_payment.py`
Константы из коллекции: `ZIP="91780"`, `IPADDR="162.251.108.36"`, `CO_CODE="def"`,
`RESELLER="qa_tester_19"`, `EPOCH_DIGEST="b1bd...._qa"`, `MASTERCODE="M-607039"`,
`INVOICE_PRODUCT_MAP` (siteId → invoiceProductNNN).

---

## Фаза 3 — `payment_client.py` (HTTP-слой)

`PaymentClient(BaseApiClient)` — тонкие методы, каждый = один запрос коллекции:

| Метод | Запрос |
|---|---|
| `auth(email, password)` | POST `auth_payment` → сохраняет atoken через `set_bearer_token` |
| `get_sale_event(event, event_id)` | GET `join_sale_event` |
| `get_prices(category, tab)` | GET `join_prices` (+ query event/event_id) |
| `create_payment_url(payload)` | POST `payment_url_new` |
| `create_payment_url_exist(payload)` | POST `payment_url_exist` (re-join) |
| `epoch_sync_json(body)` | POST `epoch_sync` (FlexPost, JSON) |
| `epoch_sync_form(data)` | POST `epoch_sync` (DataPlus/Cancel, form-urlencoded) |
| `invoice_status(invoice_uuid)` | GET `invoice_status` |
| `dashboard_info()` | GET `dashboard_info` |
| `get_upgrade_rules()` | GET `upgrade_rules` |
| `get_flexgrade_invoice(payload)` | POST `upgrade_url_epoch` |
| `get_easy_cancel_url(membership_uuid)` | GET `easy_cancel_upgrade_url` |

Парсеры ответов (отдельные функции/staticmethods):
- `parse_prices(json, category, tab, group)` → `TariffPrice`
- `parse_payment_url(json)` → `PaymentResult` (dynamic vs old format)
- `parse_dashboard(json)` → member_id, membership_uuid, status

Свойство контура:
- `self_host` → `urlparse(self.base_url).netloc` — «свой» хост текущего контура (для self-separated бандла). Не хардкодим `sg.vrporn.com`.

> `epoch_sync_form` шлёт `application/x-www-form-urlencoded` — нужно временно переопределить content-type сессии (по умолчанию JSON), либо передать `data=` и подменить заголовок.

---

## Фаза 4 — `epoch_payloads.py` (тела запросов)

Функции-билдеры (чистые, без HTTP):
```python
def build_flexpost_body(session, *, bundle=False) -> dict   # JSON, ~30 полей
def build_dataplus_form(session, tx_type, *, amount=None, ref_ids="0",
                        is_master=False) -> dict             # form, ets_*
def build_cancel_form(session) -> dict                       # form, mcs_*
def build_flexgrade_form(session, gate_type, kind="upgrade") -> dict
```
Типы DataPlus: `I`, `N`, `F`, `T`, `U`, `O`, `C`. Логика инкремента tx и `ref_trans_ids` для рефанда — здесь.

---

## Фаза 5 — `payment_flow.py` (оркестратор)

Класс `PaymentFlow`, держит `PaymentSession` + `PaymentClient`. Высокоуровневые сценарии:

```python
def select_tariff(category, tab, event=None) -> TariffPrice   # Layer 01
def standard_join(price) -> PaymentSession                    # L02/01: create→flexpost→invoice→DataPlus[I]
def free_trial_join(price)                                    # L02/02: F→U→N
def paid_trial_join(price)                                    # L02/03: T→U→N
def lifetime_join(price)                                      # L02/04: O
def rejoin_inactive(price)                                    # L02/05
def login_and_load_state(email, password)                     # auth + dashboard
def rebill()                                                  # DataPlus[N]
def upgrade()                                                 # L03/01
def easy_cancel_downgrade()                                   # L03/02
def refund()                                                  # L03/03
def assert_membership_active() / refresh_dashboard()
```

Каждый шаг логирует на русском (как принято) и обновляет `session`.

---

## Фаза 6 — `test/test_payment.py`

```python
@pytest.mark.payment
class TestTariffs:          # Layer 01
    def test_sale_event_default_guest(...)
    def test_get_prices_categories(...)

@pytest.mark.payment
class TestJoins:            # Layer 02
    @pytest.mark.parametrize("category,tab", [...])
    def test_standard_join_and_rebill(...)
    def test_free_trial_flow(...)
    def test_paid_trial_flow(...)
    def test_lifetime_one_time(...)
    def test_rejoin_inactive(...)

@pytest.mark.payment
class TestChanges:          # Layer 03
    def test_upgrade_flexgrade_and_rebill(...)
    def test_easy_cancel_downgrade(...)
    def test_refund(...)
```

Фикстуры в `test/conftest.py`:
- `payment_env` — контур из `--environment` (default `VRP_STAGE`); валидируем, что это VRP-секция
- `payment_flow` — собранный `PaymentFlow(environment=payment_env)`
- `pay_user` — учётка из `.env` (для Layer 03 / re-join)

CLI-флаги (добавить в `pytest_addoption`): `--pay-category`, `--pay-tab`, `--pay-event` (опционально, есть дефолты).

Мульти-контур в тестах:
- один прогон = один контур через `--environment`;
- тест-код не содержит хардкод-хостов — всё через `payment_flow` (резолв `base_url` из секции).

---

## Фаза 7 — Документация + мульти-контур runner

- `services/payment/README.md` — запуск, ENV, сценарии, таблица контуров.
- `run_payment_contours.py` (корень, по образцу `run_*.py`) — последовательный прогон выбранных контуров:
  ```bash
  python run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE
  ```
  PROD в дефолт не входит, добавляется только явно.
- Обновить `CLAUDE.md` — добавить 4-й трек «Payment tests» + примеры запуска по контурам.
- Обновить `ai/PROJECT_REPORT.md` — новый сервис в карте.

---

## Порядок выполнения и проверка

1. Фаза 0 (ТЗ) → согласовать.
2. Фазы 1–2 (конфиг + модели/fakes/config) — изолированно, можно юнит-тестировать `fakes.py` (`inc_tx`, `money`).
3. Фаза 3–4 (client + payloads).
4. Фаза 5 (flow).
5. Фаза 6: запускаем `pytest -m payment --environment=VRP_STAGE -v`.
6. Прогон сначала Layer 01 (smoke, без записи), затем 02, затем 03.

**Риск-контроль:** реальные транзакции идут с `isTest=true`. Прогонять только на `VRP_STAGE` (`sg.vrporn.com`), не на PROD без явного запроса.

---

## Открытые вопросы (не блокируют старт, уточним по ходу)

1. `epoch_pst_type` (MC/VS) — берём дефолт MC, вынесем в флаг при необходимости.
2. `active_epoch_pi_code` после upgrade — читать из dashboard/upgrade-rules после смены тарифа.
3. Bundle-сценарий: в текущей коллекции явного bundle-join в Layer нет (только утилиты блокировки тарифов). Реализуем bundle-ветку в `build_flexpost_body`, но тест добавим только если найдём рабочий сценарий.
