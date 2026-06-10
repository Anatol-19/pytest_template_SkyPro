# План готовности к тестам бандлов (VRP)

> Дата: 2026-06-10. Источники: Postman `Payment_final.json` (скрипты Get Prices + Create URL +
> FlexPost), Docmost `Bundle price Description`, живой ответ `/prices` и `/user-sale-event` на TEST.
> Бизнес-логика — `ai/VRP_BUSINESS_LOGIC.md`. Это план; код пока не меняем, ждём event-ключи.

---

## 1. Референс из Postman — как устроен bundle

### Шаг A. Sale Event задаёт состав бандла
`GET /proxy-user/api/memberships/join-now/user-sale-event?event=<KEY>` возвращает:
```
bundleType:   "standard" | "super" | ...
bundledSites: [ { host: "vrconk.com", ... }, ... ]   # какие slave-сайты в бандле
```
> На TEST сейчас (без event-ключа): `bundleType=standard`, `bundledSites=[vrporn.com]` (self).

### Шаг B. Get Prices — сборка additionalIds (Postman test-script)
Для каждого `host` из `bundledSites`:
- **self** (`vrporn.com` / `<self_host>`) → `price.specialPrice.vrbPriceMembershipId` → в `additionalIds` (это и есть self-separate/токены);
- **slave** → найти в `price.price_slave_sites` по `siteHost` → `slave.uuid` → в `additionalIds`; `slave.epochPiCode` → в `slavePicodes[slug]` (slug = host без `.com`).

Итог: `join_additional_subscription_ids`, `join_is_bundle`, `join_bundle_slave_picodes`.

Поля реального slave (TEST, подтверждено): `uuid`, `siteHost`, `epochPiCode`, `epochSite`, `handlerUrl`, `isSeparatedBundle`.

### Шаг C. Create Payment URL
```json
{ ..., "subscr_id": "<master membership_id>", "slavePriceUuids": <additionalIds> }
```
> `additionalSubscriptionId` бэк отвергает в new-member флоу (строка `""` только в re-join `-exist`).
> Slave uuids идут в `slavePriceUuids`.

### Шаг D. FlexPost [M] (bundle-ветка)
```
x_is_master_site = "true"
pi_code          = invoiceProduct{master_site_id}    # флаг Dynamic Price, НЕ реальный PiCode
x_pi_code        = <master epoch_pi_code>             # реальный
x_bundle_master_vrporn = <master epoch_pi_code>
x_bundle_slave_{slug}  = <slave epochPiCode>          # для каждого slave
```
Slave-транзакции Epoch рассылает сам (Default Separated Bundle). Нам — один master FlexPost.

---

## 2. Текущее состояние кода

| Узел | Статус |
|---|---|
| FlexPost bundle-поля (`build_flexpost_body`, `session.is_bundle`, `bundle_slave_picodes`) | ✅ есть, но никто не заполняет |
| `MASTER_INVOICE_PRODUCT` / `INVOICE_PRODUCT_MAP` (`config_payment.py`) | ✅ есть (хардкод `invoiceProduct158529` = sg VRBS) |
| Резолв `bundledSites` → `slavePriceUuids` + slave picodes | ❌ нет |
| Передача `slavePriceUuids` в `create_payment_url` | ❌ сейчас всегда `[]` |
| Self-separate (токены) + Data+ на master И slave | ❌ нет |
| Тесты бандлов | ❌ нет |

Вывод: каркас есть, не хватает связки **sale event → price slaves → create url → flexpost**.

---

## 3. План реализации (3 требования)

### Требование 1 — возможность покупки бандлов (по event-ключам)
1. `get_sale_event(event=KEY)` → взять `bundledSites[].host` + `bundleType`.
2. Новый метод `payment_client.build_bundle(price, bundled_hosts, self_host)`:
   - вернуть `slave_uuids[]` + `slave_picodes{slug: epochPiCode}` по правилам Шага B;
   - self_host резолвится из `base_url` (контур-агностично).
3. `select_tariff(..., bundle=True/event=KEY)` → заполнить `session.is_bundle`, `bundle_slave_picodes`, `session.slave_uuids`.
4. `create_payment_url(..., slave_uuids=session.slave_uuids)`.
5. `standard_join` уже шлёт FlexPost — bundle-поля подхватятся из session.
6. Тест-класс `TestBundleJoins`: параметризация по event-ключам (mono / bundle / super).

**Нужно от тебя:** event-ключи для `?event=` (какие sale events дёргать: моно-бандл, бандл, супер-бандл, self-separate).

### Требование 2 — простые покупки идут дефолтным методом, даже если в sale event есть бандл
- Bundle включается **только явным opt-in** (`--pay-bundle` / отдельный тест-класс).
- По умолчанию `select_tariff` **игнорирует** `bundledSites`: `slavePriceUuids=[]`, FlexPost без bundle-полей — обычный Standard/Dynamic флоу.
- Тест-гард: `TestJoins` (простые) не должны слать `slavePriceUuids` и `x_bundle_*`, даже если sale event с бандлом. Проверка: лог/ассерт `session.is_bundle is False`.

### Требование 3 — Self-separate (токены)
Особенности (с твоих слов + Docmost «Self Separated Bundle»):
- В `get-recurring-payment` добавляется иначе: self-host → не slave-uuid, а **специальная цена/токен-membership** (Postman: `specialPrice.vrbPriceMembershipId`).
- ⚠️ Реальный прайс на TEST отдаёт поле **`special_prices`** (snake, массив), а Postman читает **`specialPrice.vrbPriceMembershipId`** (camel). **Расхождение — сверить точное поле/структуру** на self-separate sale event.
- Data+ нужно слать на **оба**: Master premium **и** Slave tokens (тот же роут `/api/payment/sync-handler/epoch`, т.к. это тоже мы). То есть в симуляции:
  - FlexPost [M] (master) → DataPlus[I] master premium → **DataPlus[I] slave tokens** → (ребиллы N для подписки; токены — разовые, S/O без ребилла).
- Новый метод `self_separate_join`: после master DataPlus отправить отдельный DataPlus для токен-слейва (свой `member_id`/`tx`/`pi_code`).
- ⚠️ Admin-дока (02-04-1): «Self Separated bundle with Tokens **не реализованы** на 03.06.2026» — возможно, бэк ещё не готов. Уточнить статус на тестируемом контуре.

---

## 4. Открытые вопросы (нужны ответы/ключи перед кодом)

1. **Event-ключи** для `?event=`: какие значения вызывают моно-бандл / бандл / супер-бандл / self-separate? (на TEST дефолтный sale event даёт self `vrporn.com`).
2. **Master invoiceProduct по контурам**: сейчас хардкод `invoiceProduct158529` (sg VRBS). Для `t.vrporn`/`d.vrporn` — тот же или другой `master_site_id`? Где взять (поле прайса `used_as_master_on_sites`?).
3. **Self-separate поле**: `special_prices` (реальный ответ) vs `specialPrice.vrbPriceMembershipId` (Postman) — какая структура актуальна?
4. **Data+ для self-separate**: подтвердить набор транзакций для токен-слейва (тип `S`/`O`, отдельный `member_id`? тот же? отдельный `pi_code` токена `crvrrw35p1334320` из примеров?).
5. **Super bundle**: отличается ли тело FlexPost (3+ slave) от обычного, кроме числа `x_bundle_slave_*`?

---

## 5. Дорожная карта внутри bundle-этапа
1. Получить event-ключи → проверить `get_sale_event(event=KEY)` отдаёт ожидаемые `bundledSites`.
2. Реализовать резолв slaves + `slavePriceUuids` + FlexPost bundle-поля → `TestBundleJoins` (mono/bundle/super).
3. Гард простых покупок (Требование 2).
4. Self-separate (токены) + двойной Data+ (Требование 3) — после сверки полей и статуса бэка.
5. Обновить `ai/VRP_PAYMENT_TESTING.md` / `PAYMENT_RUN_COMMANDS.md`.
