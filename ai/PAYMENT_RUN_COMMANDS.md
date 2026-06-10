# Payment — команды запуска

> Контур по умолчанию `VRP_STAGE`. Ниже примеры на `VRP_TEST` (t.vrporn.com).
> Меняй `--environment` на `VRP_DEV` / `VRP_STAGE` / `VRP_PROD` по необходимости.
> Все команды из корня проекта. Allure включён по умолчанию (пишет в `Reports/allure`).

Префикс для всех команд:
```bash
cd /Users/aqa/PycharmProjects/pytest_template_SkyPro
```

---

## Базовые кейсы покупок (всегда с ребиллом)

Все используют один тест `test_standard_join_and_rebill` (Join → FlexPost → DataPlus[I] →
Dashboard → DataPlus[N]). Тариф выбирается флагом `--pay-tab`.

### Standard прайс (кейсы 1–3)

```bash
# 1. Месячный тариф (standard) + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=monthly -v

# 2. Годовой тариф (standard) + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=yearly -v

# 3. Lifetime тариф (standard) + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=lifetime -v
```

### Special прайс (кейсы 4–6)

Спец-цены берутся отдельным запросом внутри той же прайс-группы:
`?type_prices_from_slot=N&event_id=<uuid>&event=` (`event_id` — uuid текущего Sale Event,
подтягивается автоматически). Номер слота задаётся `--pay-slot` (пример: `2`).

```bash
# 4. Месяц special + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=monthly --pay-slot=2 -v

# 5. Год special + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=yearly --pay-slot=2 -v

# 6. Lifetime special + ребилл
.venv/bin/python -m pytest "test/test_payment.py::TestJoins::test_standard_join_and_rebill" \
  --environment=VRP_TEST --pay-tab=lifetime --pay-slot=2 -v
```

> Примечание по lifetime: тест делает recurring-join (DataPlus[I]+[N]) на lifetime-цене.
> Если бэкенд для lifetime не ожидает ребилл — это как раз то, что покажет прогон, анализируй ответ.
> (Есть отдельный `TestJoins::test_lifetime_one_time` — чистый One-Time DataPlus[O] без ребилла.)
>
> Про `--pay-slot`: номер слота (`2` в примерах с фронта) — уточни актуальный по контуру.
> Sale event как механизм выбора прайс-группы НЕ реализован (используем текущий).

---

## Просмотр результата

К каждому тесту в лог и в Allure пишется сводка сессии (email, member_id, membership_uuid,
invoice_uuid, статус, tx) — для сверки на фронте и в админке.

```bash
# отчёт с историей/трендом + открыть в браузере
bash tools/allure_report.sh

# быстрый просмотр
bash tools/allure_report.sh --serve
```

---

## Дорожная карта (следующие шаги)

1. **Отдельные функциональные тесты** на операции Layer 03:
   - Cancel
   - Upgrade
   - Downgrade (Easy Cancel)
2. **Дефолтный E2E-сценарий** (одна цепочка):
   `join → rebill → cancel → rebill → upgrade → rebill → easy-cancel → rebill → refund`
3. **Кейсы с бандлами** (bundle-прайсы, slave-сайты).
4. **Тест Segpay** (альтернативный платёжный шлюз помимо Epoch).
