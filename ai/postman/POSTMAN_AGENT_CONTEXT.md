# Postman-агент — контекст и роль

> Точка входа для Claude Code, работающего с Postman-коллекцией.
> Читай этот файл первым. Потом — только те доки, которые нужны для задачи.

---

## Кто я и что делаю

Я — агент, который:
1. Читает Python-реализацию (`services/payment/`, `test/test_payment.py`)
2. Отражает её в Postman-коллекции (`Payment_final.json`)
3. Запускает прогоны через Newman
4. Синхронизирует коллекцию с Postman cloud

Python-реализация — **источник истины**. Постман идёт вслед за ней, не опережает.

---

## Второй агент (не я)

Реализует Python-автотесты. С ним пользователь обсуждает логику тестирования и утверждает флоу.
Я читаю то, что он реализовал, и переношу в коллекцию.

**Не дублируй** обсуждение бизнес-логики — она уже в `ai/VRP_BUSINESS_LOGIC.md`.
**Не переписывай** `ai/VRP_PAYMENT_TESTING.md` — это ТЗ второго агента.

---

## Файлы, которые я читаю

| Файл | Зачем |
|---|---|
| `test/test_payment.py` | Сценарии: какие методы вызываются, в каком порядке |
| `services/payment/payment_client.py` | Эндпоинты, тела запросов, параметры |
| `services/payment/epoch_payloads.py` | Тела FlexPost / DataPlus / Cancel / FlexGrade |
| `services/payment/models.py` | Структуры данных (TariffPrice, PaymentSession) |
| `services/payment/config_payment.py` | Константы: SALE_EVENT_KEYS, sandbox-параметры |
| `ai/POSTMAN_ANALYSIS.md` | Разбор реальной коллекции (живые прогоны) |
| `ai/postman/NEWMAN_COMMANDS.md` | Команды запуска |
| `ai/postman/CLOUD_SYNC.md` | Синхронизация с Postman cloud |

---

## Файлы, которые я пишу / редактирую

- `/Users/aqa/Documents/postman-work/Payment_final.json` — коллекция
- `/Users/aqa/Documents/postman-work/run_env.json` — env-переменные для Newman
- `/Users/aqa/Documents/postman-work/sync_to_cloud.sh` — скрипт синка

---

## Как читать Python → Postman

### Метод payment_flow → папка в коллекции

| Python-метод | Папка в коллекции |
|---|---|
| `select_tariff()` | `Layer 01 — Tariffs` |
| `standard_join()` / `bundle_join()` / `lifetime_join()` | `Layer 02 — Joins / 01 Standard Recurring` и т.д. |
| `rebill()` | DataPlus[N] в том же сценарии |
| `upgrade()` / `easy_cancel_downgrade()` | `Layer 03 — Changes` |
| `finalize()` | Cancel + DataPlus[C] в конце сценария |
| `segpay_join()` / `segpay_rebill()` | Segpay-папки (отдельный слой) |

### Тело запроса → Postman request body

Тело берётся из `epoch_payloads.py` / `segpay_payloads.py`.
Динамические значения (`member_id`, `transaction_id`) → переменные окружения `{{...}}` или pre-request script.

### Assert в Python → Test script в Postman

```python
# Python
assert payment_flow.refresh_dashboard().get("status"), "мембер должен быть активен"

# Postman test
pm.test("мембер активен", () => {
    const d = pm.response.json();
    pm.expect(d.data[0].info.status).to.be.ok;
});
```

---

## Чего не делаю

- Не создаю новые сценарии без Python-реализации
- Не изменяю бизнес-логику — только отражаю
- Не синхронизирую с cloud без явной просьбы пользователя
