# Анализ Postman-коллекции Payment_final.json

> Дата анализа: 2026-06-10  
> Источник: `/Users/aqa/Documents/postman-work/Payment_final.json`  
> Env: `/Users/aqa/Documents/postman-work/run_env.json`  
> Статус: **первичный анализ перед реализацией**

---

## ⚠️ Критические расхождения с ТЗ

ТЗ (`VRP_PAYMENT_TESTING.md`) содержит несколько принципиальных ошибок.  
Реальная коллекция отличается в следующем:

---

### 1. Epoch НЕ вызывается напрямую

ТЗ утверждало: `POST https://bs.epoch.com/flexpost` и `POST https://bs.epoch.com/dataplus`.

**Реальность:** все Epoch-запросы идут через **бэкенд-прокси**:
```
POST https://{{Base_url}}/api/payment/sync-handler/epoch
```
Никакого прямого обращения к `bs.epoch.com` нет. `EpochClient` из ТЗ — несуществующая сущность.

---

### 2. Все URL отличаются от ТЗ

| Операция | ТЗ (неверно) | Реальный URL |
|---|---|---|
| Sale Event | `/api/sale-event` | `/proxy-user/api/memberships/join-now/user-sale-event` |
| Prices | `/memberships/prices` | `/proxy-user/api/memberships/prices` |
| Create Payment URL | `/api/payment/url` | `/api/memberships/join-now/get-recurring-payment-url` |
| Re-join (expired) | — | `/api/memberships/join-now/get-recurring-payment-url-exist` |
| FlexPost / DataPlus | `bs.epoch.com/flexpost`, `bs.epoch.com/dataplus` | `/api/payment/sync-handler/epoch` |
| Invoice Status | — | `/api/payment/invoice/status?invoice_uuid=...` |
| Dashboard / Membership | `/api/user/membership` | `/proxy-user/api/wp/user/dashboardInfo` |
| Upgrade Rules | — | `/proxy-user/api/memberships/service/price-upgrade-rules` |
| Upgrade Invoice | `/api/payment/upgrade-url` | `/proxy-user/api/payment/recurring-upgrade-url/epoch` |
| Easy Cancel | `/api/payment/easy-cancel-url` | `/proxy-user/api/easy-cancel/upgrade-url?membershipUuid=...` |
| Auth | `/proxy-user/api/wp/auth/login` | `/api/wp/secure/auth/login` |

> **Примечание по Auth:** `/proxy-user/api/wp/auth/login` — это путь из `routes.ini` для мемберского логина в content tests. Auth для payment — другой endpoint: `/api/wp/secure/auth/login`.

---

### 3. Структура ответа `/prices` — dict, не list

ТЗ: массив тарифов.  
Реальность:
```json
{
  "prices": {
    "bundle": [ {...}, {...} ],
    "standard": [ {...}, {...} ]
  }
}
```
Выборка тарифа по цепочке: `prices[category]` → фильтр по `price_tab.slug` → фильтр по `price_groups[].slug`.  
Ключевые поля тарифа: `membership_id` (а не `uuid`), `epoch_pi_code` (а не `pi_code`).  
Цена: `trial_price ?? price ?? rebill_price`.

---

### 4. Структура Sale Event отличается

ТЗ: `{bundleType, bundledSites[]}`.  
Реальность:
```json
{
  "uuid": "a530354f-...",
  "saleEventGroup": 1,
  "userRegionCode": "US"
}
```
Параметры запроса: `?event_id={uuid}&event={event}` (uuid берётся из предыдущего шага или env).  
Bundle-хосты и slave UUIDs ТЗ описывало — это другой API (более старый?).

---

### 5. FlexPost — JSON через прокси, много полей

ТЗ описывало form-encoded запрос напрямую к Epoch.  
Реальность: **JSON POST** через прокси со следующими полями:
```python
{
    "email": user_email,
    "username": user_email,
    "member_id": fake_member_id,       # '4219' + rnd(9)
    "transaction_id": fake_tx_id,      # '108qa' + rnd(6)
    "pi_code": epoch_pi_code,
    "x_pi_code": epoch_pi_code,
    "trans_amount": amount,
    "trans_amount_usd": amount,
    "amount": amount,
    "localamount": amount,
    "order_id": fake_member_id,
    "event_datetime": unix_timestamp,
    "ans": f"YQATEST|{transaction_id}",
    "reseller": "qa_tester_19",
    "name": username,
    "postalcode": "91780",
    "zip": "91780",
    "co_code": "def",
    "country": "US",
    "ipaddress": "162.251.108.36",
    "submit_count": "1",
    "trans_currency": currency,
    "currency": currency,
    "payment_type": "CC",
    "payment_subtype": "MC",           # из env epoch_pst_type (MC / VS)
    "site": "a",
    "session_id": fake_session,        # rnd(32) + '_qa'
    "epoch_digest": "b1bd4832368aa4b37c9037ff50c2e90a_qa",
    "x_invoice": invoice_uuid,
    "x_uniq_id": invoice_uuid,
    "x_user": user_uuid,
    "isTest": True
}
```
Для бандла добавляются:
```python
"x_is_master_site": "true",
"pi_code": "invoiceProduct158529",        # флаг, не реальный PiCode
"x_bundle_master_vrporn": epoch_pi_code,
"x_bundle_slave_{slug}": slave_pi_code    # для каждого slave
```
Ответ прокси: `{"status": "ok"}` (не Epoch-формат).

---

### 6. DataPlus — form-encoded через тот же прокси

Все DataPlus (I, N, F, T, U, O, C) — `POST /api/payment/sync-handler/epoch` с `Content-Type: application/x-www-form-urlencoded`.  
Поля с префиксом `ets_` (не `x_`):

| Тип | `ets_transaction_type` | Примечания |
|---|---|---|
| I — Initial Recurring | `I` | после FlexPost, `transaction_id = initial_tx_id` |
| N — Rebill | `N` | `ets_pi_code = active_epoch_pi_code`, tx = `incTx(last, 3)` |
| F — Free Trial | `F` | `prepaid = N` |
| T — Paid Trial | `T` | — |
| U — Trial Conversion | `U` | tx = `incTx(last, 3)` |
| O — One-Time | `O` | — |
| C — Chargeback/Refund | `C` | `ets_amount = -amount`, `ets_ref_trans_ids = last_dataplus_id` |

**Cancel** (не DataPlus) использует другой набор полей с префиксом `mcs_`:
```
mcs_or_idx, mcs_canceldate, mcs_cocode, mcs_picode, mcs_reseller,
mcs_signupdate, mcs_email, mcs_username, mcs_reason, mcs_memberstype, ...
```

---

### 7. Dashboard вместо /user/membership

После логина состояние мембера читается из:
```
GET /proxy-user/api/wp/user/dashboardInfo
```
Ответ: `{data: [{info: {member_id, membership_uuid, status, duration, email, ...}}]}`

Этот же запрос используется для:
- Получения `member_id` и `membership_uuid` после join
- Проверки статуса после DataPlus
- Загрузки состояния перед Upgrade/EasyCancel

---

### 8. Transaction ID — инкремент, не новая генерация

Каждый следующий DataPlus [N] увеличивает `transaction_id` на 3:
```python
def inc_tx(tx_id: str, step: int = 3) -> str:
    # '108qa000123' → '108qa000126'
    import re
    m = re.match(r'^(.*?)(\d+)$', tx_id)
    return m.group(1) + str(int(m.group(2)) + step).zfill(len(m.group(2)))
```

---

## Полная структура коллекции

```
Layer 01 — Tariffs
  01 Default — Guest
      _Scenario Config (postman-echo, только конфиг)
      00 Backend - Get Sale Event   GET /proxy-user/api/memberships/join-now/user-sale-event
      Get Join Prices               GET /proxy-user/api/memberships/prices
  02 Event — Affiliate / Card Drop
      (аналогично, с event параметрами)
  03 Expired Member
      00 Backend - Auth             POST /api/wp/secure/auth/login
      Get Sale Event
      Get Join Prices

Layer 02 — Joins
  01 Standard Recurring (I) + Rebill
      _Scenario Config
      Create Payment URL            POST /api/memberships/join-now/get-recurring-payment-url
      FlexPost [M] JSON             POST /api/payment/sync-handler/epoch  (JSON)
      Invoice Status                GET  /api/payment/invoice/status?invoice_uuid=...
      DataPlus [I]                  POST /api/payment/sync-handler/epoch  (form)
      Auth / Get JWT                POST /api/wp/secure/auth/login
      Dashboard Info                GET  /proxy-user/api/wp/user/dashboardInfo
      DataPlus [N]                  POST /api/payment/sync-handler/epoch  (form)
      Dashboard Info

  02 Free Trial (F → U → N)
      ...FlexPost → DataPlus[F] → Auth → Dashboard → DataPlus[U] → DataPlus[N]...

  03 Paid Trial (T → U → N)
      ...FlexPost → DataPlus[T] → Auth → Dashboard → DataPlus[U] → DataPlus[N]...

  04 Lifetime / One Time (O)
      ...FlexPost → DataPlus[O] → Auth → Dashboard...

  05 Inactive / Expired Re-join (I) + Rebill
      Auth → _Load State (Dashboard) → Create Payment URL (exist endpoint) →
      FlexPost → Invoice Status → DataPlus[I] → Dashboard → DataPlus[N] → Dashboard

Layer 03 — Changes
  01 Upgrade (Flexgrade) + Rebill
      Auth → _Load State → Dashboard →
      Get Upgrade Price UUID        GET  /proxy-user/api/memberships/service/price-upgrade-rules
      Get Flexgrade Invoice         POST /proxy-user/api/payment/recurring-upgrade-url/epoch
      FlexGrade [upgrade]           POST /api/payment/sync-handler/epoch  (form, ans=YQAUPGRADE|...)
      Dashboard → DataPlus[N] → Dashboard

  02 Easy Cancel Downgrade + Rebill
      Auth → _Load State → Dashboard →
      Easy Cancel Upgrade URL       GET  /proxy-user/api/easy-cancel/upgrade-url?membershipUuid=...
      FlexGrade [downgrade]         POST /api/payment/sync-handler/epoch  (form)
      Dashboard → DataPlus[N] → Dashboard

  03 Refund (C)
      Auth → _Load State →
      Cancel [cancel]               POST /api/payment/sync-handler/epoch  (form, mcs_ fields)
      DataPlus [C]                  POST /api/payment/sync-handler/epoch  (form, отрицат. сумма)
      Dashboard

_Utils
  Universal Epoch DataPlus JSON / FORM   (ручные утилиты)
  [UnZip] - Начисления                   GET api-stag.unzipvr.com (внешний сервис)
  [Bundle] - Блокировка тарифов          POST /api/memberships/bundle-prices/{pi_code}/used/{Slave_Site}
  [Bundle] - Разблокировка тарифов       DELETE /api/memberships/bundle-prices/{pi_code}/used/{siteHost}
```

---

## Что нужно переосмыслить в реализации

### Архитектура сервиса

ТЗ предлагало разделить на `PaymentClient` + `EpochClient`. На практике:
- `EpochClient` как отдельного HTTP-клиента **не нужен** — всё через прокси
- Разумнее: один `PaymentClient(BaseApiClient)` + dataclass-модели

### Генерация fake-данных

```python
import random, time, re

def fake_member_id() -> str:      return '4219' + ''.join([str(random.randint(0,9)) for _ in range(9)])
def fake_transaction_id() -> str: return '108qa' + ''.join([str(random.randint(0,9)) for _ in range(6)])
def fake_session_id() -> str:     return ''.join([str(random.randint(0,9)) for _ in range(32)]) + '_qa'
def epoch_time() -> str:          return str(int(time.time()))
def inc_tx(tx_id: str, step: int = 3) -> str:
    m = re.match(r'^(.*?)(\d+)$', tx_id)
    return m.group(1) + str(int(m.group(2)) + step).zfill(len(m.group(2)))
```

### Структура данных сессии

Нужен объект состояния, который накапливается по ходу флоу:
```python
@dataclass
class PaymentSession:
    email: str
    password: str
    # После Get Prices
    price_uuid: str         # membership_id тарифа
    epoch_pi_code: str
    amount: str
    currency: str
    # После Create Payment URL
    invoice_uuid: str
    user_uuid: str
    # После FlexPost
    member_id: str
    transaction_id: str
    initial_transaction_id: str
    # После Auth + Dashboard
    atoken: str
    membership_uuid: str
    member_status: str
    # Для rebill
    last_dataplus_id: str
    active_pi_code: str     # может измениться после upgrade
    active_amount: str
```

### Новые маршруты в routes.ini

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
bundle_lock             = /api/memberships/bundle-prices/{pi_code}/used/{slave_site}
```

---

## Вопросы, требующие уточнения перед реализацией

1. **Bundle в Layer 01** — коллекция не содержит явного bundle-сценария в Layer 01 с `bundledSites`. Реально ли это нужно или это legacy API?
2. **`join_price_category`** — default `"bundle"` в env, но при standard join, видимо, `"standard"`. Нужно ли параметризовать?
3. **`epoch_pst_type`** (MC / VS) — влияет ли на реальный тест, или всегда MC?
4. **`active_epoch_pi_code` для DataPlus [N]** — откуда берётся после upgrade? Нужно ли читать из Dashboard после каждого Upgrade?
5. **Re-join (`get-recurring-payment-url-exist`)** — нужен ли аутентифицированный заголовок или тот же анонимный запрос?
6. **Scope маркера `payment`** — покрывать все 3 Layer (тарифы + join + changes) или только join?
