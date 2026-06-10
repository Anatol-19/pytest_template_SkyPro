# VRP — бизнес-логика оплат (источник: Docmost)

> Источник истины: Docmost, space **VR Porn** (`019b5a09-8083-75f0-b1dd-d3fb4ebda4b6`),
> раздел **00 Business Process Logic** + **04 VRP-USER (Bangercave) → 02. Memberships**.
> Дата выгрузки: 2026-06-10. Это конспект авторитетных статей — при расхождении с кодом
> приоритет у Docmost (но платёжные тела сверять с рабочей Postman-коллекцией, см. ниже).

Ключевые страницы Docmost:
- `02-02. Sale Event` — `019bb280-9d20-7a21-a09c-75e8a1560188`
- `02-03 Price Groups` — `019bb280-a032-79c3-bcb2-c428c69d6fb6`
- `02-04. Prices` / `02-04-1. New or Edit price` — `019bb280-a314-...` / `019bb288-08e3-...`
- `02-05. Upgrade Prices` — `019bb280-a668-7127-b8b4-7338551ebf45`
- `Epoch Payment System` — `019d6383-f34a-7425-9345-c54f8b7c733f`
- `Epoch → Примеры тел транзакций` — `019d7256-9321-7937-8aaf-038df3d9d96a`
- `Segpay Payment System` — `019d63ca-a99a-7277-95a6-0fcc5a9e0f44`
- `Payment Types` — `019d63a0-b09d-7985-9c52-7471e566657b`
- `Bundle price Description` — `019bb288-0f9e-76ac-9ee8-c35dc34cb1b0`

---

## 1. Выбор прайса: Sale Event → Price Group → Slot (Standard/Special)

**Sale Event** — управляет выбором **прайс-группы** для показа мемберу. Сам по триггеру
выбирает, какую прайс-группу отдать. Триггеры и приоритет:

| Группа | Триггер |
|---|---|
| DropCard | query-параметр в ссылке (admin: URL parameter) |
| Holiday | даты + чекбокс `active` |
| Expired | статус подписки в токене мембера |
| Affiliate | query-параметр (от UnZip) |
| Default | даты + чекбокс `active` |

Event срабатывает, если: (1) сработал его триггер и (2) нет другого event выше по приоритету.
Bundle-настройки (Bundle Sites, Bundle Type Default/Super, Hide bundle) тоже на уровне Sale Event.

**Price Group** — набор готовых тарифов для Sale Event. **Каждый слот в группе делится на
`Standard Price` и `Special Price`.** Переключение standard↔special происходит запросом
с `type_prices_from_slot`:

```
Standard:  GET /proxy-user/api/memberships/prices
Special:   GET /proxy-user/api/memberships/prices?type_prices_from_slot=<N>&event_id=<sale_event_uuid>&event=
```

> В фреймворке: выбор прайс-группы через Sale Event **НЕ автоматизирован** (используем текущий).
> Переключение Standard/Special реализовано флагом `--pay-slot=<N>` (`type_prices_from_slot`),
> `event_id` берётся из текущего Sale Event.

---

## 2. Типы транзакций Epoch (Payment Types)

| Тип | Код | Назначение |
|---|---|---|
| INITIAL (FlexPost / Postback) | `M` | первичная авторизация на шлюзе |
| INITIAL RECURRING | `I` | старт рекуррентной подписки (DataPlus) |
| INITIAL FREE TRIAL | `F` | старт бесплатного триала |
| TRIAL | `T` | платный триал / cross-sale |
| INITIAL TRIAL CONVERSION | `U` | конверсия триала в подписку |
| RECURRING | `N` | ребилл |
| ONE TIME | `O` | разовый платёж / lifetime |
| ONE TIME TOKEN | `S` | разовая покупка токенов |
| CANCEL | `cancel` | отмена (поля `mcs_*`) |
| REFUND | `C` | возврат; **обязателен `ref_trans_ids`**, сумма отрицательная |
| CHARGEBACK | `D` | чарджбэк |
| UPGRADE | `upgrade` | апгрейд (Flexgrade) |
| DOWNGRADE | `downgrade` | даунгрейд (Flexgrade); доп. поле `x_vip_offer=Y` |
| RETENTION | `retention` | информационная транзакция об изменении amount |

Классификация по рекуррентности:
- **Join**: M, I, T, F, O, S, upgrade, downgrade
- **Rebill**: U, N
- **Refund**: C, D

Покрыто в коде (`services/payment/epoch_payloads.py`): M, I, F, T, U, N, O, cancel, C, upgrade, downgrade.
**Не покрыто**: S (One Time Token), D (Chargeback), retention.

---

## 3. Epoch — методы интеграции (справочно)

Шлюз: данные карты собираются на стороне Epoch (PCI). Основные API:
- **FlexPost™** — своя форма подписки, карта вводится на странице Epoch. Сессия ~10 мин.
- **Data Plus** — фид транзакций (новые, отмены, кредиты, чарджбэки, ребиллы, конверсии), задержка ~15 мин.
- **Flexgrade** — upgrade/downgrade в рамках одного мастеркода. POST на `https://www.epoch.com/secure/flexgrade.cgi`. Обязательны `member_id`, `username`, `ti_code`. Сессия 30 мин.
- **Dynamic Pricing API** (JWT Bearer): `invoice-push`, `billing-modify`, `customer-push`, `billing/upgrade`.
- CamCharge, MemberPlus, CancelPlus, CSAPI, Reactivation API — пока вне scope тестов.

`epoch_digest` — HMAC-MD5 хэш для проверки целостности (несовпадение → `NMYSERVNOTALLOWED`).
Тестовые карты Epoch → `YGOODTEST`; полный флоу — рандомные approve/deny без реального списания.

Коды отказа (частые): `NDECLINED`, `NMYCEH` (уже есть мемберство), `NMYDUPLICATE`,
`NMYSESSIONEXPIRED` (форма не отправлена 30 мин), `NMYINVPICODE`, `NMYINVMEMBERID`,
`NMYMISSINGUPGRADETYPE` (нет ti_code), `NMYNOUPGRADEOFFERED` (ti_code не активен).

---

## 4. Upgrade / Downgrade (Flexgrade) — ограничения

- Работает **только между recurring-тарифами**. Для Lifetime на стороне Epoch заводят
  спец-рекуррентные тарифы (9999 мес, 0 ребилл).
- Нужен **Ti Code** нового тарифа (через саппорт Epoch).
- **Не работает с Dynamic Pricing** (Epoch отвечает 500).
- Сценарии биллинга: **Extended** (полная цена + продление даты) / **Pro-Rated** (пропорционально).
- Роут получения инвойса: `proxy-user/api/payment/recurring-upgrade-url/epoch`.
- Колбэк (Data+): `ans`, `local_amount`, `amount`, `currency`, `transaction_id`, `member_id`,
  `x_gate_type=flexgrade`, `x_invoice`, `x_membership_id`.

---

## 5. Segpay — второй в каскаде

**Каскад:** Epoch первый → если Epoch отклонил → редирект на **Segpay** → если Segpay тоже
отклонил (`approved=no`) → назад на фронт (`x-decl-link`), **без дальнейшего каскада**.

- Сущности: **Price Point**, **Package**, **Postback**, **SRS API** (SOAP: отмены/возвраты/отчёты), **Processing API** (платёжные ссылки через query-параметры).
- Типы транзакций: Sale, Rebill, Refund, Chargeback, Cancel.
- Поля постбэка: `purchaseid`, `tranid`, `approved` (yes/no), `trantype`, `stage`.
- Платёжная ссылка: `x-billemail`, `username`, `memberID`, `x-auth-link` (success), `x-decl-link` (fail), `paypagelanguage`, `DMC=1` (мультивалюта).
- Sandbox: Test Mode на Package. Карты: успех `4111 1111 1111 1111`, отказ `4000 0000 0000 0002`.
- **Upgrade**: цена $1.00–$500.00, срок 30–9999 дней, **деньги списываются без подтверждения карты**.
- **Cancel**: авто-отмена отключена на всех продуктах — пользователь отменяет вручную через страницу Segpay.
- PCI DSS (карта хранится у Segpay), 3DS по банку, токенизация, антифрод (F440–V3012).
- ⚠️ Не тестировать в LIVE без согласования — влияет на score мерчанта.

> Тест Segpay в фреймворке **ещё не реализован** (запланирован после бандлов).

---

## 6. Bundle-связки (для будущих тестов)

- **Inner Bundle** — устаревшее, не применяется (1 транзакция на общую сумму, управление через мастер-подписку).
- **Separated Bundle (Default)** — мастер передаёт набор тарифов шлюзу; slave-сайты сами обрабатывают свои транзакции; управление подписками независимое. Мастер шлёт FlexPost с `x_is_master_site=true`, slave-транзакции Epoch рассылает сам.
- **Super Separated Bundle** — от 3 сайтов.
- **Self Separated Bundle** — подписка + токены (один сайт у нас, раздельные на стороне шлюза). **Self Separated с токенами не реализовано** на проекте (на 03.06.2026).

`pi_code=invoiceProduct{siteId}` в FlexPost бандла — флаг Dynamic Price (не реальный PiCode);
реальный PiCode в `x_pi_code`; `x_bundle_master_*` / `x_bundle_slave_{slug}` — аналитика.

> Тесты бандлов в фреймворке **ещё не реализованы** (следующий этап после E2E).

---

## 7. Расхождения Docmost ↔ Postman-коллекция (требуют сверки при тестах)

Платёжные тела в коде портированы из рабочей **Postman-коллекции `Payment_final.json`** (VRP,
проверена на живом TEST — мембер становится Active). Примеры тел в Docmost — частично generic/VRB
(`ets_co_code=VRB`, тестовые `ans`). Поэтому код **не переписываем под Docmost вслепую**; ниже —
точки, которые стоит перепроверить при реальных прогонах соответствующих операций:

| # | Docmost (пример) | Код (из Postman) | Статус |
|---|---|---|---|
| 1 | Upgrade `ans="YGOODTEST\|OK"` | `ans="YQAUPGRADE\|{tx}"` | сверить при тесте upgrade |
| 2 | Downgrade `ans="YDOWNGRADED"` + `x_vip_offer="Y"` | `ans="YQADOWNGRADE\|{tx}"`, без `x_vip_offer` | сверить при тесте downgrade |
| 3 | DataPlus `ets_payment_type` = `A`/`B`, `ets_pst_type`=`MC`/`VS`/`PP` | `ets_payment_type="CC"`, `ets_pst_type="MC"` | работает на TEST; сверить семантику |
| 4 | `ets_co_code` = `VRB` (в примерах) | `VRP` | для VRP корректно `VRP` |
| 5 | Типы `S`, `D`, `retention` | не реализованы | добавить при необходимости |

Вывод: Docmost — авторитет по **бизнес-логике** (флоу, сущности, ограничения, каталог типов).
Точные **тела запросов** для VRP — по Postman-коллекции, подтверждённой живыми прогонами.
