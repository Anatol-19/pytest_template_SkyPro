---
name: lighthouse
description: >
  Run Lighthouse performance tests and CrUX data collection for VRP/VRS environments.
  Use this skill whenever the user wants to: run performance tests, check page speed,
  collect CrUX data, check test job status, see available environments or routes,
  says "запусти лайтхаус", "проверь скорость", "перф тест", "запусти сатурацию",
  "статус джобы", "какие контуры есть". Invoke proactively for any performance
  testing topic even without an explicit command.
---

# Lighthouse MCP Skill

Доступ к Lighthouse MCP серверу для перф-тестирования VRP/VRS платформ.
Результаты пишутся в Google Sheets.

## Инструменты

| Tool | Когда использовать |
|------|-------------------|
| `lighthouse_get_status` | Проверить: CLI установлен? GSheets подключён? Текущий контур? |
| `lighthouse_list_environments` | Список контуров (VRP_DEV/TEST/STAGE/PROD, VRS_DEV/TEST/STAGE/PROD) |
| `lighthouse_list_routes` | Список роутов из routes.ini |
| `lighthouse_run_lighthouse` | **Синхронный** запуск CLI — блокирует до завершения, подходит для 1-2 роутов |
| `lighthouse_run_crux` | **Синхронный** сбор CrUX (только PROD-контуры) |
| `lighthouse_enqueue_lighthouse` | Поставить CLI-задачу в очередь → сразу job_id |
| `lighthouse_enqueue_api` | Поставить API-задачу (PageSpeed Insights) в очередь → job_id |
| `lighthouse_enqueue_crux` | Поставить CrUX в очередь → job_id |
| `lighthouse_enqueue_environment_saturation` | Все роуты × все устройства через CLI |
| `lighthouse_enqueue_api_saturation` | Все роуты × все устройства через API |
| `lighthouse_list_jobs` | Посмотреть все задачи в очереди |
| `lighthouse_job_status` | Статус и результат конкретной задачи по job_id |

## Когда sync, когда enqueue

**Sync (`run_lighthouse`, `run_crux`)** — если роутов 1-2 и пользователь готов ждать.
**Enqueue** — всегда когда роутов много или запускается сатурация. Сразу возвращай job_id
и предложи проверить статус позже через `job_status`.

## Типичные сценарии

### "Запусти тест для главной страницы"
```
enqueue_lighthouse(routes=["home"], device="desktop", environment="VRP_PROD")
→ возвращаю job_id, говорю что запущено
```

### "Полная сатурация"
```
enqueue_environment_saturation(environment="VRP_PROD")
→ запускает все роуты × desktop + mobile
```

### "Какой статус джобы abc123?"
```
job_status(job_id="abc123")
```

### "CrUX для прода"
CrUX доступен только для *_PROD контуров. Если контур не PROD — предупреди.

## Параметры

- **device**: `"desktop"` или `"mobile"`
- **iterations**: кол-во прогонов (по умолчанию 5 для enqueue, 10 для sync)
- **environment**: контур из `list_environments`. Если не указан — используется текущий
- **sprint** / **tag**: опциональные метки для Google Sheets, если не переданы — берутся из dashboard автоматически
