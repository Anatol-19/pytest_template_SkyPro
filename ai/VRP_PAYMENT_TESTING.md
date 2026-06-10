# VRP Payment Testing — ТЗ (переписано по реальной коллекции)

> Дата: 2026-06-10 (ревизия 3)  
> Источники истины:
> - **Бизнес-логика** (флоу, сущности, ограничения, типы транзакций) — Docmost, конспект в `ai/VRP_BUSINESS_LOGIC.md`.
> - **Тела запросов для VRP** — Postman-коллекция `Payment_final.json` + `run_env.json` (подтверждено живыми прогонами на TEST). Детальный разбор: `ai/POSTMAN_ANALYSIS.md`.
> - **Команды запуска** — `ai/PAYMENT_RUN_COMMANDS.md`.
> 
> Реализация: `services/payment/` + `test/test_payment.py`.
>
> ⚠️ Самая первая версия содержала ошибки (прямые вызовы `bs.epoch.com`, неверные URL,
> неверная структура ответов). Исправлено по фактической коллекции + Docmost.

---

## 1. Главное отличие от первой версии

**Epoch напрямую не вызывается.** Все «эпоховские» запросы (FlexPost, DataPlus, Cancel,
FlexGrade) идут через бэкенд-прокси одного эндпоинта:

```
POST {base_url}/api/payment/sync-handler/epoch
```

Отдельного `EpochClient` к `bs.epoch.com` нет и не нужно.

---

## 2. Контуры

Коллекция полностью параметризована переменной `{{Base_url}}`. Поддерживаются все 4 VRP-контура
(уже описаны в `URLs/base_urls.ini`):

| Контур | Секция | host |
|---|---|---|
| Dev | `VRP_DEV` | `d.vrporn.com` |
| Test | `VRP_TEST` | `t.vrporn.com` |
| Stage | `VRP_STAGE` | `sg.vrporn.com` |
| Prod | `VRP_PROD` | `vrporn.com` |

Контур задаётся флагом `--environment`. Весь тест-код контур-агностичен; единственный «свой»
хост (для self-separated бандла) резолвится динамически из `base_url`.

Все транзакции отправляются с `isTest=true`. PROD из дефолтного мульти-прогона исключён.

---

## 3. Реальные эндпоинты

| Операция | Метод | Путь |
|---|---|---|
| Sale Event | GET | `/proxy-user/api/memberships/join-now/user-sale-event` |
| Prices | GET | `/proxy-user/api/memberships/prices` |
| Create Payment URL (new) | POST | `/api/memberships/join-now/get-recurring-payment-url` |
| Create Payment URL (re-join) | POST | `/api/memberships/join-now/get-recurring-payment-url-exist` |
| Epoch sync (FlexPost/DataPlus/Cancel/FlexGrade) | POST | `/api/payment/sync-handler/epoch` |
| Invoice Status | GET | `/api/payment/invoice/status?invoice_uuid=...` |
| Auth (JWT) | POST | `/api/wp/secure/auth/login` |
| Dashboard / Membership | GET | `/proxy-user/api/wp/user/dashboardInfo` |
| Upgrade rules | GET | `/proxy-user/api/memberships/service/price-upgrade-rules` |
| Flexgrade Invoice | POST | `/proxy-user/api/payment/recurring-upgrade-url/epoch` |
| Easy Cancel URL | GET | `/proxy-user/api/easy-cancel/upgrade-url?membershipUuid=...` |

---

## 4. Запросы и структуры данных

### 4.1 Sale Event
`GET /proxy-user/api/memberships/join-now/user-sale-event[?event_id=..&event=..]`
Ответ: `{ "uuid": "...", "saleEventGroup": 1, "userRegionCode": "US" }`

### 4.2 Prices
```
Standard:  GET /proxy-user/api/memberships/prices
Special:   GET /proxy-user/api/memberships/prices?type_prices_from_slot=<N>&event_id=<sale_event_uuid>&event=
```
Sale Event выбирает **прайс-группу**; внутри группы каждый слот делится на Standard/Special
(см. `ai/VRP_BUSINESS_LOGIC.md` §1). Переключение реализовано флагом `--pay-slot=<N>`.

Ответ — **dict по категориям** (ключ задаёт бэкенд, на TEST обычно один — `bundle`):
```json
{ "prices": { "bundle": [ {price} ] } }
```
Выбор тарифа (`parse_prices`): категория = первая доступная → фильтр по `price_tab.slug == tab`
с нормализацией алиасов (`year→yearly`, `month→monthly`, `life→lifetime`); если таб не найден —
явная ошибка (не «первый молча»).
Поля тарифа: `membership_id` (= subscr_id), `epoch_pi_code`, цена = `trial_price ?? price ?? rebill_price`,
валюта `price_currency || currency || "USD"`.

### 4.3 Create Payment URL
`POST /api/memberships/join-now/get-recurring-payment-url`
```json
{
  "affiliate": "", "email": "<email>", "email_marketing": true, "js_hit": "",
  "module": "epoch", "password": "<password>", "subscr_id": "<membership_id>",
  "slavePriceUuids": [], "uuid": ""
}
```
Ответ:
- **Dynamic URL (бандл):** `{ "paymentUrl": "...", "invoiceUuid": "...", "userUuid": "..." }`
- **Старый формат:** `{ "paymentUrl": "...?x_invoice=..&x_user=.." }` — парсим query.

Re-join (`...-url-exist`) — то же тело + `"additionalSubscriptionId": ""` (строка).

### 4.4 FlexPost [M] — JSON через прокси
`POST /api/payment/sync-handler/epoch` (Content-Type: application/json)
Полное тело — см. `POSTMAN_ANALYSIS.md` §5. Fake-данные (`member_id`, `transaction_id`,
`session_id`) генерируются на стороне клиента. Для бандла добавляются `x_is_master_site`,
`pi_code=invoiceProduct{siteId}`, `x_bundle_master_*`, `x_bundle_slave_{slug}`.
Ответ прокси: `{ "status": "ok" }`.

### 4.5 DataPlus — form-urlencoded через прокси
`POST /api/payment/sync-handler/epoch` (Content-Type: application/x-www-form-urlencoded)
Поля с префиксом `ets_`. Тип задаётся `ets_transaction_type`:

| Тип | Назначение | Особенности |
|---|---|---|
| `I` | Initial Recurring | tx = initial_transaction_id |
| `N` | Rebill | `ets_pi_code = active`, tx = `inc_tx(last, 3)` |
| `F` | Free Trial | prepaid=N |
| `T` | Paid Trial | — |
| `U` | Trial Conversion | tx = `inc_tx(last, 3)` |
| `O` | One-Time / Lifetime | — |
| `C` | Refund/Chargeback | amount = `-amount`, `ets_ref_trans_ids = last_dataplus_id` |

### 4.6 Cancel — form-urlencoded
Поля с префиксом `mcs_` (`mcs_or_idx`, `mcs_picode`, `mcs_email`, `mcs_reason`, `mcs_memberstype=R`, ...).

### 4.7 FlexGrade (Upgrade / Downgrade) — form-urlencoded
Поля: `ans=YQAUPGRADE|{tx}`, `member_id`, `transaction_id`, `x_gate_type`, `x_invoice`,
`x_membership_id`, `amount`, `currency`, `isTest=true`.
Перед этим — Flexgrade Invoice / Easy Cancel URL, откуда берём `x_invoice`, `gate_type`, `ti_code`.

> Ограничения Flexgrade (Docmost): только recurring-тарифы, нужен `ti_code` нового тарифа,
> **не работает с Dynamic Pricing**. Расхождения по `ans` (Docmost: `YGOODTEST|OK` / `YDOWNGRADED`
> + `x_vip_offer=Y`) — см. `ai/VRP_BUSINESS_LOGIC.md` §7, сверить при реальном тесте.

### 4.8 Invoice Status / Dashboard
- `GET /api/payment/invoice/status?invoice_uuid=..` → `{status, purchase_type, url_redirect}`.
- `GET /proxy-user/api/wp/user/dashboardInfo` → `{data:[{info:{member_id, membership_uuid, status, duration, email}}]}`.

---

## 5. Сценарии (Layer 01–03)

### Layer 01 — Tariffs
- L01/01 Default Guest: Sale Event → Get Prices
- L01/02 Event (Affiliate/Card Drop): Sale Event(event) → Get Prices(event)
- L01/03 Expired Member: Auth → Sale Event → Get Prices

### Layer 02 — Joins
- L02/01 Standard Recurring (I) + Rebill: CreateURL → FlexPost[M] → Invoice Status → DataPlus[I] → Auth → Dashboard → DataPlus[N] → Dashboard
- L02/02 Free Trial: ...FlexPost → DataPlus[F] → Auth → Dashboard → DataPlus[U] → DataPlus[N]
- L02/03 Paid Trial: ...FlexPost → DataPlus[T] → Auth → Dashboard → DataPlus[U] → DataPlus[N]
- L02/04 Lifetime / One-Time: ...FlexPost → DataPlus[O] → Auth → Dashboard
- L02/05 Inactive/Expired Re-join: Auth → Dashboard → CreateURL(exist) → FlexPost → Invoice → DataPlus[I] → Dashboard → DataPlus[N] → Dashboard

### Layer 03 — Changes
- L03/01 Upgrade (Flexgrade) + Rebill: Auth → Dashboard → Upgrade Rules → Flexgrade Invoice → FlexGrade[upgrade] → Dashboard → DataPlus[N] → Dashboard
- L03/02 Easy Cancel Downgrade + Rebill: Auth → Dashboard → Easy Cancel URL → FlexGrade[downgrade] → Dashboard → DataPlus[N] → Dashboard
- L03/03 Refund (C): Auth → Dashboard → Cancel[cancel] → DataPlus[C] → Dashboard

---

## 6. Реализация в Python

См. `ai/PAYMENT_IMPLEMENTATION_PLAN.md`. Кратко:
```
services/payment/
├── models.py          # TariffPrice, PaymentResult, PaymentSession
├── fakes.py           # fake_member_id/transaction_id/session_id, inc_tx, money, transaction_date
├── config_payment.py  # ZIP, IPADDR, CO_CODE, RESELLER, EPOCH_DIGEST, MASTERCODE, INVOICE_PRODUCT_MAP
├── payment_client.py  # PaymentClient(BaseApiClient) + парсеры + self_host
├── epoch_payloads.py  # build_flexpost_body / build_dataplus_form / build_cancel_form / build_flexgrade_form
└── payment_flow.py    # PaymentFlow — оркестратор сценариев
```

`.env`:
```dotenv
VRP_PAY_EMAIL=...        # учётка мембера для Layer 03 / re-join
VRP_PAY_PASSWORD=...
```

Маркер: `@pytest.mark.payment`. Запуск:
```bash
pytest -m payment --environment=VRP_STAGE -v
python run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE
```

---

## 7. Ловушки

| # | Нюанс | Решение |
|---|---|---|
| 1 | Epoch только через прокси `/api/payment/sync-handler/epoch` | Нет прямых вызовов bs.epoch.com |
| 2 | `/prices` — dict по категориям, поле `membership_id` (не `uuid`) | Парсер `parse_prices` |
| 3 | Create URL: dynamic (`invoiceUuid` в JSON) vs old (query params) | Проверять наличие `invoiceUuid` |
| 4 | FlexPost — JSON; DataPlus/Cancel — form-urlencoded | Разные content-type на одном URL |
| 5 | `pi_code=invoiceProduct{id}` для бандла — флаг, не реальный PiCode | Реальный PiCode в `x_pi_code` |
| 6 | tx_id для N/U инкрементируется (`inc_tx`, +3), не генерируется заново | `fakes.inc_tx` |
| 7 | Self-separated хост зависит от контура | `urlparse(base_url).netloc`, не хардкод |
| 8 | `additionalSubscriptionId` — строка `""`, не `[]` (re-join) | Использовать строку |
| 9 | Refund: отрицательная сумма + `ets_ref_trans_ids=last_dataplus_id` | build_dataplus_form('C') |
| 10 | UnZip (`api-stag.unzipvr.com`) — внешний staging-сервис из _Utils | Вне scope |
| 11 | Sale Event = выбор **прайс-группы** (триггеры DropCard/Holiday/Expired/Affiliate/Default) | Не автоматизируем — используем текущий; `event_id` берём для special-цен |
| 12 | Standard/Special — слоты прайс-группы через `type_prices_from_slot` | Флаг `--pay-slot=<N>` |
| 13 | Lifetime = Non-Recurring (One Time, тип `O`) — **ребилла нет** | Lifetime → `test_lifetime_one_time`, не join+rebill |
| 14 | Upgrade/Downgrade только recurring; Lifetime — спец-рекуррент (9999 мес); нужен Ti Code; не Dynamic Pricing | Учитывать при выборе тарифа для upgrade-теста |
| 15 | Segpay — второй в каскаде (Epoch → Segpay); тест не реализован | См. `VRP_BUSINESS_LOGIC.md` §5 |
| 16 | Типы `S` (token), `D` (chargeback), `retention` — не покрыты | Добавить при необходимости |

Полная бизнес-логика (Epoch/Segpay/бандлы/типы транзакций) — `ai/VRP_BUSINESS_LOGIC.md`.
