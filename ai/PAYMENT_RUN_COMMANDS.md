# Payment — команды запуска

> Контур по умолчанию `VRP_STAGE`. Меняй `--environment` на `VRP_DEV`/`VRP_TEST`/`VRP_STAGE`/`VRP_PROD`.
> Allure включён по умолчанию (`Reports/allure`). Все транзакции `isTest=true`.
> Полная матрица кейсов — `ai/PAYMENT_CASES_MATRIX.md`.

Запускать из корня проекта. Путь на macOS: `/Users/aqa/PycharmProjects/pytest_template_SkyPro/`.
На Windows: `C:\Study\pytest_template_SkyPro\`. Активируй venv перед запуском.

## Full-run (все 11 кейсов)

```bash
python -m pytest -m payment --environment=VRP_STAGE -v
```
Каждая цепочка завершается Cancel→Refund (lifetime — только Refund); самосепарат чистит master+токен.
Прогон на STAGE ~6.5 мин (11 passed, 1 skipped — re-join в бэклоге).

## По группам

```bash
# Покупки (месяц/год) + rebill → Cancel→Refund
python -m pytest "test/test_payment.py::TestUserJoins::test_join_recurring" --environment=VRP_STAGE -v

# Lifetime (O) → Refund
python -m pytest "test/test_payment.py::TestUserJoins::test_join_lifetime" --environment=VRP_STAGE -v

# Бандлы / самосепарат (master): mono/bundle/super/self/ss/sos
python -m pytest "test/test_payment.py::TestUserJoins::test_join_bundle" --environment=VRP_STAGE -v

# Изменения: upgrade / downgrade (Flexgrade)
python -m pytest "test/test_payment.py::TestUserChanges::test_change_and_rebill" --environment=VRP_STAGE -v
```

## Отдельный кейс (по id параметризации)

```bash
python -m pytest "test/test_payment.py::TestUserJoins::test_join_recurring[monthly]" --environment=VRP_STAGE -v
python -m pytest "test/test_payment.py::TestUserJoins::test_join_bundle[self-0-True]" --environment=VRP_STAGE -v
python -m pytest "test/test_payment.py::TestUserChanges::test_change_and_rebill[upgrade]" --environment=VRP_STAGE -v
```

## Мульти-контур

```bash
python test/run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE
```

## Отчёт Allure (история/тренд)

```bash
# macOS
brew install allure              # однократно
bash tools/allure_report.sh      # генерация + открыть
bash tools/allure_report.sh --serve

# Windows
# allure установить отдельно (scoop install allure или скачать zip)
bash tools/allure_report.sh
```

К каждому тесту в лог и Allure прикладывается сводка сессии (email, member_id, membership_uuid,
invoice_uuid, статус, tx) — для сверки в админке.

---

## Флаги выбора тарифа

| Флаг | Назначение |
|---|---|
| `--pay-tab` | monthly\|yearly\|lifetime (алиасы year/month/life) |
| `--pay-slot` | Standard (пусто) / Special N (`type_prices_from_slot`) |

Бандлы задаются в тесте через `select_tariff(event=KEY, bundle=True)` (ключи: mono/bundle/super/self/ss/sos).
Простая покупка (`bundle=False`) игнорирует бандл sale event — дефолтный метод.
