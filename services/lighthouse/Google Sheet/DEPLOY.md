# Деплой Google Apps Script — инструкция

## Структура

```
services/lighthouse/Google Sheet/   ← исходники (редактируем тут)
  PerfAnalytics.gs                  ← дашборд
  Formatter.gs                      ← форматирование
  DailyApiRunner.gs                 ← ежедневный мониторинг

tools/clasp/                        ← рабочая директория clasp
  .clasp.json                       ← привязка к Google Script проекту
  appsscript.json                   ← манифест (таймзона, макросы)
  PerfAnalytics.gs.js               ← копия для деплоя
  Formatter.js                      ← копия для деплоя
  DailyApiRunner.gs.js              ← копия для деплоя
```

## Шаги деплоя

### 1. Скопировать изменённые файлы в clasp

Из корня проекта (`C:\Study\pytest_template_SkyPro`):

```bash
# PerfAnalytics
cp "services/lighthouse/Google Sheet/PerfAnalytics.gs" tools/clasp/PerfAnalytics.gs.js

# Formatter (если менялся)
cp "services/lighthouse/Google Sheet/Formatter.gs" tools/clasp/Formatter.js

# DailyApiRunner (если менялся)
cp "services/lighthouse/Google Sheet/DailyApiRunner.gs" tools/clasp/DailyApiRunner.gs.js
```

### 2. Запушить в Google Apps Script

```bash
cd tools/clasp
clasp push
```

Clasp спросит подтверждение — ответить `y`.

### 3. Проверить деплой

```bash
clasp open
```

Откроется редактор Apps Script в браузере — убедиться что код обновился.

### 4. Запустить дашборд

В Google Sheets:
- Меню **QA Dashboard → Generate Dashboard**
- Или кнопка **Generate Dashboard** на листе Dashboard

## Быстрая команда (всё разом)

```bash
cp "services/lighthouse/Google Sheet/PerfAnalytics.gs" tools/clasp/PerfAnalytics.gs.js && cd tools/clasp && clasp push && cd ../..
```

## Откат

Если что-то сломалось:

```bash
# Посмотреть версии
clasp versions

# Откатить к предыдущей версии в редакторе
clasp open
# → File → Version history → Restore
```

Или из git:

```bash
git log --oneline -- "services/lighthouse/Google Sheet/PerfAnalytics.gs"
git checkout <commit-hash> -- "services/lighthouse/Google Sheet/PerfAnalytics.gs"
# Затем повторить деплой
```

## Важно

- **НЕ редактировать** файлы напрямую в `tools/clasp/` — они перезаписываются при копировании
- Исходники всегда в `services/lighthouse/Google Sheet/`
- `clasp pull` затянет изменения ИЗ Google обратно в `tools/clasp/` (полезно если кто-то правил в браузере)
- Script ID: `1LBwr7Jz0xiYYBJsW1eVkH0-UCOWpWHnlOb8Pae4-yOfK2TDC5ZkOFu5l`
