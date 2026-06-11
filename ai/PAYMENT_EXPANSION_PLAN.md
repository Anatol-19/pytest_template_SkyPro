# План расширения payment-тестов VRP

> Дата: 2026-06-10. Источники: Postman `Transaction.postman_collection.json` (другой проект —
> берём только тела/методы), Docmost (`ai/VRP_BUSINESS_LOGIC.md`), текущая реализация (List A).
> Бэк/роуты — наши, как обсуждали. Все цепочки завершаются хвостом **Cancel → Refund** (как в List A).
> Утверждённый scope: Segpay + Centrobill; Epoch +Chargeback/CrossSale/Member+/CamCharge/slave. Приоритет — **Segpay первым**.

## Роуты бэка (проверено на VRP_STAGE 2026-06-10)
- `/api/memberships/join-now/get-recurring-payment-url` + `module:"segpay"` — **создание инвойса Segpay** (НЕ `/api/account` — это роут смежного проекта, на VRP отдаёт SPA).
- `/api/payment/sync-handler/segpay` — основной флоу транзакций ✅ (есть; на пустое тело 500).
- `/api/payment/recurring-upgrade-url/segpay` — upgrade ✅ (нужны auth+membership).
- `/api/payment/handler/centrobill` — Centrobill ✅.
- **`/handler/` == `/sync-handler/`** — одно и то же, разница в синхронной обработке vs очередь (берём `sync-handler` за основу, `handler` по необходимости).

Создание инвойса Segpay возвращает `paymentUrl` (`secure2.segpay.com/billing/poset.cgi`), из которого парсим:
`invoiceId`, `x-eticketid` (`<prefix>:<segpay_ti_code>`), `x_user`, `x-auth-link`, `x-decl-link`.

---

## Фаза 1 — Segpay (приоритет)

**Подход (без каскада, пока так):** запрашиваем `get-recurring-payment-url` с `module:"segpay"` →
получаем готовую Segpay-ссылку, из неё берём `invoiceId`/`eticketid`/`pplist`. Каскад Epoch→Segpay
не моделируем. Этого достаточно для всех Segpay-кейсов: джойны, ребиллы, апгрейды.

Модель транзакции: **один form-постбэк на событие** (нет M+DataPlus), тип = `trantype`
(Sale/Credit/Charge) + `stage` (Initial/Conversion).

**Маппинг полей (коллекция → наша сторона):** многие поля чужой коллекции схлопываются в наши:
- `paymentaccountid` ≈ **invoice** (invoiceUuid)
- `invoiceid` = invoiceUuid; `eticketid`/`pplist` — из paymentUrl
- `purchaseid` = member_id (fake, как в Epoch); `tranid` = transaction_id (fake)
- `merchantid/urlid/postbackconfiguniqueid` — из коллекции, правим по ошибкам бэка
- `cancelreasoncode/refundreasoncode` — из публичной доки Segpay

### Файлы
- `URLs/routes.ini`: `segpay_sync = /api/payment/sync-handler/segpay`, `upgrade_url_segpay = /api/payment/recurring-upgrade-url/segpay` (инвойс — через существующий `payment_url_new` с `module:"segpay"`).
- `services/payment/config_segpay.py` — константы. ⚠️ `merchantid/urlid/postbackconfiguniqueid/paymentaccountid` в коллекции — от **смежного проекта**, для VRP нужны реальные (уточнить). `billzip`, `merchantname`, card-поля — дефолтные.
- `services/payment/segpay_payloads.py` — билдеры форм:
  - `build_initial` — `stage=Initial, trantype=Sale, approved=Yes`
  - `build_recurring` — `stage=Conversion, trantype=Sale`
  - `build_cancel` — `action=Cancel, cancelreasoncode`
  - `build_refund` — `trantype=Credit, price=-amount, relatedtranid={last}`
  - `build_chargeback` — `trantype=Charge, price=-amount, authcode`
  - ключевые поля: `tranid`, `purchaseid`(member), `invoiceid`, `eticketid="…:{segpay_ti_code}"`, `authprice/price/ival/rval`, `x-auth-link/x-decl-link`
- `services/payment/payment_client.py`: `create_account(...)` (POST `/api/account`), `segpay_sync_form(data)`.
- `PaymentFlow`: ветка `payment_system="segpay"` или `segpay_join()`; `segpay_ti_code` берём из прайса (`price.segpay_ti_code`).

### Кейсы (full-run Segpay)
| Кейс | Транзакции | Статус |
|---|---|---|
| Segpay recurring + rebill | Create(module=segpay) → Initial(Sale) → Recurring(Conversion) → **Cancel → Refund(Credit)** | ✅ `TestSegpay`, прошёл на STAGE |
| Segpay upgrade | New Upgrade (`recurring-upgrade-url/segpay`) → upgrade-postback | 🔴 **не прогоняется синтетически**: маршрут делает живой вызов Segpay API (`Segpay/ApiClient.php:46` → `Undefined index isSuccess`); Old Upgrade postback без него → `error`. Методы готовы (epoch-стиль тело, `/proxy-user/`, auth, target ti-код есть). Нужен backend-sandbox Segpay или живой шлюз. Тест — skip. |
| Segpay One-Click (Member+) | Initial OneClick → Recurring → Cancel → Refund | ⏳ |
| Segpay chargeback | … → Charge (альт. хвост к Refund) | builder готов (`build_chargeback`) |
| (опц.) каскад Epoch→Segpay | — | не моделируем (по решению) |

Реализовано: `config_segpay.py`, `segpay_payloads.py` (initial/recurring/cancel/refund/chargeback),
`PaymentClient.segpay_sync_form` + `parse_segpay_extras` + `create_payment_url(module=)`,
`PaymentFlow.segpay_join/segpay_rebill/segpay_finalize`, `fakes.segpay_date()`.
Нюанс: Segpay-хендлер отвечает строкой `"OK"`; дата — `MM/DD/YYYY hh:MM:SS AM/PM`.

---

## Фаза 2 — Epoch: доп-флоу (тот же epoch-слой)

| Кейс | Статус | Примечание |
|---|---|---|
| **Chargeback (D)** | ✓ в scope | добавить тип `D` в `build_dataplus_form` (отриц. сумма); альт. хвост к Refund |
| **CrossSale** (M/T/U/N/C/D) | ✓ в scope | `ans="Y…,{tx},CAPTURED|{member}"`, доп-продажа |
| **CamCharge / токены (S)** | ✓ только **отправка** | реально получить метод от бэка можно лишь при настоящей оплате на Epoch — мы только симулируем отправку |
| **Slave-сторона бандла** | ✓ в scope | Master M + **Slave M + Slave D+** — когда мы slave принимаем транзакции master-сайта |
| ~~Member+~~ | ✗ исключён | на проекте не актуален |

> `/handler/epoch` == `/sync-handler/epoch` (синхронная обработка vs очередь) — берём `sync-handler`
> за основу, `handler` используем по необходимости. Отдельный route не обязателен.

---

## Фаза 3 — Centrobill

Разовые платежи (Docmost: `non_recurring_price`, мин $14.95). Роут `/api/payment/handler/centrobill`
(тело уточнить в коллекции при реализации). Кейс: разовая покупка → (рефанд если поддерживается).

---

## Фаза 4 — Sale Events (разблокирует бэклог)

Базовый функционал выбора прайс-группы (триггеры DropCard/Holiday/Expired/Affiliate/Default) →
открывает Layer 01 Tariffs, re-join (`TestExpiredMember`), управляемый выбор special-цен.

---

## Бэклог (доп.)

- **Фабрика тестовых мемберов нужного состояния** — атомарные методы получения пользователей для
  фронта: Active определённого тарифа, Cancelled, через Dynamic Pricing и обычные. Переиспользуемые
  хелперы (не полный сценарий), чтобы быстро готовить юзеров в нужном статусе.
- CCBill, GoCoin — вне scope сейчас.

---

## Архитектурное решение
- `PaymentFlow` параметризовать платёжной системой (`payment_system="epoch"|"segpay"`) ИЛИ ввести
  `SegpayFlow`; epoch-код (`epoch_payloads.py`) не трогаем.
- Хвост `finalize()` (Cancel→Refund) — общий контракт для всех систем (у Segpay: Cancel + Credit).
- Тест-данные тарифа: Epoch — `epoch_pi_code`; Segpay — `segpay_ti_code` (оба уже в ответе `/prices`).
- Маркер `@pytest.mark.payment`; отдельные классы `TestSegpay…`, расширение `TestUserJoins` для Epoch-флоу.

## Порядок
1. **Segpay** (account + sync-handler/segpay + upgrade) → `TestSegpay` full-run на STAGE.
2. **Epoch доп**: Chargeback(D), CrossSale, Member+/CamCharge(S), slave-сторона.
3. **Centrobill** (разовый).
4. **Sale Events** (+ Layer 01, re-join, special-группы).

## Открытые вопросы к реализации (уточнить по ходу)
1. `/api/account` — точная структура ответа (где invoice uuid / member). Проверим на STAGE.
2. Segpay `paymentaccountid` — два значения (Initial/Conversion): фиксированные на контур или из ответа?
3. Каскад Epoch→Segpay — как воспроизвести Epoch-decline в тесте (спец-карта/флаг)?
4. Centrobill — тело запроса (в коллекции запрос есть, нужно извлечь при реализации).
5. Slave-сторона: на каком контуре/хосте мы выступаем slave (handlerUrl slave-сайта).
