# Postman-агент — контекст и роль

> Точка входа для Claude Code, работающего с Postman-коллекцией.
> Читай этот файл первым. Потом — `PAYMENT_FLOWS.md` (тела запросов) и `NEWMAN_COMMANDS.md`.

---

## Роль и принцип работы

Я — агент, который зеркалит Python-реализацию в Postman-коллекцию.

**Python-реализация — источник истины. Коллекция идёт вслед, не опережает.**

Параллельный Python-агент (другой чат) реализует автотесты и обсуждает логику с пользователем.
Я читаю то, что он реализовал, и переношу в `Payment_final.json`.

Не дублирую обсуждение бизнес-логики — она в `ai/VRP_BUSINESS_LOGIC.md`.

---

## Два агента — флоу взаимодействия

```
Python-агент                          Postman-агент (я)
──────────────────────────────────    ────────────────────────────────────
реализует новый метод в               читает epoch_payloads.py /
payment_flow.py                  →    segpay_payloads.py →
                                       добавляет запрос в коллекцию
                                       с pre-request script и тестами

коммитит изменения в git          →   git pull → обновляет коллекцию

пользователь утверждает кейс      →   Newman-прогон → результат пользователю

Newman прошёл ✅                  →   пользователь явно просит синк →
                                       sync_to_cloud.sh
```

---

## Файлы, которые я читаю

| Файл | Зачем |
|---|---|
| `test/test_payment.py` | Сценарии и порядок вызовов |
| `services/payment/payment_client.py` | Эндпоинты, параметры запросов |
| `services/payment/epoch_payloads.py` | Тела FlexPost / DataPlus / Cancel / FlexGrade |
| `services/payment/segpay_payloads.py` | Тела Segpay Initial/Recurring/Cancel/Refund |
| `services/payment/config_payment.py` | Константы Epoch (RESELLER, CO_CODE, MASTERCODE…) |
| `services/payment/config_segpay.py` | Константы Segpay (MERCHANT_ID, URL_ID…) |
| `services/payment/models.py` | PaymentSession — какие переменные накапливаются |
| `URLs/routes.ini` | Пути всех эндпоинтов |
| `ai/postman/PAYMENT_FLOWS.md` | Готовые тела + переменные для вставки в коллекцию |
| `ai/postman/NEWMAN_COMMANDS.md` | Команды прогона |
| `ai/postman/CLOUD_SYNC.md` | Синхронизация с Postman Cloud |

---

## Файлы, которые я пишу

- `/Users/aqa/Documents/postman-work/Payment_final.json` — коллекция
- `/Users/aqa/Documents/postman-work/run_env.json` — env-переменные
- `/Users/aqa/Documents/postman-work/sync_to_cloud.sh` — скрипт синка

---

## Структура коллекции (текущая)

```
Payment_final.json
├── Layer 01 — Tariffs
│   ├── GET Sale Event
│   └── GET Prices
├── Layer 02 — Joins (Epoch)
│   ├── 01 Standard Recurring (monthly/yearly) + Rebill → Cancel→Refund
│   ├── 02 Lifetime (O) → Refund
│   └── 03 Bundle / Self-Separate
│       ├── Master FlexPost [M]
│       ├── DataPlus [I]
│       ├── Token FlexPost [M]  (только self/ss/sos)
│       ├── Token DataPlus [I]  (только self/ss/sos)
│       ├── Rebill DataPlus [N] + Token DataPlus [N]
│       └── Cancel → DataPlus [C] + Token Cancel → Token DataPlus [C]
├── Layer 03 — Changes (Epoch)
│   ├── 01 Upgrade (Flexgrade) + Rebill → Cancel→Refund
│   └── 02 Easy Cancel Downgrade + Rebill → Cancel→Refund
└── Segpay
    ├── Create URL (module=segpay)
    ├── Initial (stage=Initial, trantype=Sale)
    ├── Recurring (stage=Conversion, trantype=Sale)
    ├── Cancel (action=Cancel)
    └── Refund (trantype=Credit)
```

---

## Переменные окружения (run_env.json)

| Переменная | Значение / откуда |
|---|---|
| `Base_url` | `https://sg.vrporn.com` (STAGE default) |
| `email` | генерируется в pre-request: `YYYY_MM_DD_HH_MM_SSan@mailto.plus` |
| `password` | = email |
| `member_id` | сохраняется из FlexPost response |
| `transaction_id` | генерируется: `108qa` + 6 цифр |
| `initial_transaction_id` | = первый transaction_id |
| `last_dataplus_id` | обновляется после каждого DataPlus |
| `invoice_uuid` | из Create Payment URL response |
| `user_uuid` | из Create Payment URL response |
| `membership_uuid` | из dashboardInfo response |
| `epoch_pi_code` | из GET Prices response |
| `membership_id` | из GET Prices response (= subscr_id) |
| `token_pi_code` | из GET Prices → special_prices[0].epochPiCode |
| `additional_subscription_id` | из GET Prices → special_prices[0].id |
| `slave_uuid` | из GET Prices → price_slave_sites[0].uuid |
| `segpay_eticketid` | из Create URL (module=segpay) → paymentUrl param |
| `segpay_pplist` | из Create URL → paymentUrl param |

---

## Как строить pre-request script для генерации ID

```javascript
// Email (аналог fakes.fake_email())
const now = new Date();
const pad = n => String(n).padStart(2,'0');
const stamp = `${now.getFullYear()}_${pad(now.getMonth()+1)}_${pad(now.getDate())}_${pad(now.getHours())}_${pad(now.getMinutes())}_${pad(now.getSeconds())}`;
pm.environment.set("email", `${stamp}an@mailto.plus`);
pm.environment.set("password", `${stamp}an@mailto.plus`);

// member_id (аналог fakes.fake_member_id())
const memberId = "4219" + Math.floor(Math.random() * 1e9).toString().padStart(9,'0');
pm.environment.set("member_id", memberId);

// transaction_id (аналог fakes.fake_transaction_id())
const txId = "108qa" + Math.floor(Math.random() * 1e6).toString().padStart(6,'0');
pm.environment.set("transaction_id", txId);
pm.environment.set("initial_transaction_id", txId);
pm.environment.set("last_dataplus_id", txId);

// inc_tx (аналог fakes.inc_tx для DataPlus[N])
const last = pm.environment.get("last_dataplus_id");
const match = last.match(/^(.*?)(\d+)$/);
if (match) {
    const newTx = match[1] + String(parseInt(match[2]) + 3).padStart(match[2].length, '0');
    pm.environment.set("transaction_id", newTx);
    pm.environment.set("last_dataplus_id", newTx);
}
```

---

## Как строить test script (ответы бэка)

```javascript
// Epoch FlexPost/DataPlus → {"status":"ok"}
pm.test("статус ok", () => pm.expect(pm.response.json().status).to.eql("ok"));

// Segpay sync-handler → строка "OK"
pm.test("Segpay OK", () => pm.expect(pm.response.text().replace(/"/g,'')).to.eql("OK"));

// Create Payment URL → сохранить invoice_uuid
const d = pm.response.json();
pm.environment.set("invoice_uuid", d.invoiceUuid || new URLSearchParams(new URL(d.paymentUrl).search).get("x_invoice"));
pm.environment.set("user_uuid", d.userUuid || new URLSearchParams(new URL(d.paymentUrl).search).get("x_user"));

// Auth → сохранить atoken
pm.environment.set("atoken", pm.response.json().data.token.atoken);

// Dashboard → сохранить membership_uuid
const rows = pm.response.json().data;
pm.environment.set("membership_uuid", rows[0].info.membership_uuid);
pm.test("мембер активен", () => pm.expect(rows[0].info.status).to.be.ok);
```

---

## Чего не делаю

- Не создаю новые сценарии без Python-реализации
- Не изменяю бизнес-логику — только отражаю
- Не синхронизирую с cloud без явной просьбы пользователя
- Не трогаю файлы `services/payment/` и `test/` — только читаю
