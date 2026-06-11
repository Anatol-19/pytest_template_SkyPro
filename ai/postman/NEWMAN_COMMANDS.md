# Newman — команды запуска

> Newman: `/opt/homebrew/bin/newman` (v6.2.2)
> Коллекция: `/Users/aqa/Documents/postman-work/Payment_final.json`
> Env: `/Users/aqa/Documents/postman-work/run_env.json`
> Контур по умолчанию — TEST (задаётся переменной `Base_url` в `run_env.json`).

Префикс для всех команд:
```bash
cd /Users/aqa/Documents/postman-work
```

---

## Full run (вся коллекция)

```bash
newman run Payment_final.json -e run_env.json --reporters cli
```

---

## По сценарию (папке)

```bash
# Layer 02 / Standard Recurring
newman run Payment_final.json -e run_env.json \
  --folder "01 Standard Recurring (I) + Rebill"

# Layer 02 / Bundle
newman run Payment_final.json -e run_env.json \
  --folder "04 Bundle Master — FlexPost"

# Layer 03 / Upgrade
newman run Payment_final.json -e run_env.json \
  --folder "01 Upgrade (Flexgrade) + Rebill"

# Layer 03 / Refund
newman run Payment_final.json -e run_env.json \
  --folder "03 Refund (C)"
```

> Имена папок — без пути к родительскому слою. Newman ищет по первому совпадению.

---

## С HTML-репортом

```bash
# Установить репортер (однократно)
npm install -g newman-reporter-htmlextra

newman run Payment_final.json -e run_env.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export Reports/newman_report.html
```

---

## Переключение контура

Контур задаётся переменной `Base_url` в env-файле.
Значения для каждого контура:

| Контур | Base_url |
|---|---|
| DEV | `https://d.vrporn.com` |
| TEST | `https://t.vrporn.com` |
| STAGE | `https://sg.vrporn.com` |
| PROD | `https://vrporn.com` |

Переключить без правки файла — флагом `--env-var`:
```bash
newman run Payment_final.json -e run_env.json \
  --env-var "Base_url=https://sg.vrporn.com"
```

---

## Соответствие Newman ↔ pytest

| Newman (папка) | pytest |
|---|---|
| `01 Standard Recurring (I) + Rebill` | `test_join_recurring[monthly]` |
| `01 Standard Recurring (I) + Rebill` | `test_join_recurring[yearly]` |
| `04 Lifetime / One Time (O)` | `test_join_lifetime` |
| `04 Bundle Master — FlexPost` | `test_join_bundle[...]` |
| `01 Upgrade (Flexgrade) + Rebill` | `test_change_and_rebill[upgrade]` |
| `02 Easy Cancel Downgrade + Rebill` | `test_change_and_rebill[downgrade]` |
| `03 Refund (C)` | `finalize()` в конце каждого теста |
