# Структура вкладок Google Sheets

## Текущая логика

### DEV/TEST/STAGE (некритичные контуры)

| Тип проверки | Лист | Источник |
|--------------|------|----------|
| CLI | `GS_WORKSHEET_{ENV}` | Локальный Lighthouse |
| API | `GS_WORKSHEET_{ENV}` | PageSpeed API |
| CrUX | `GS_WORKSHEET_CHUX` | CrUX (28 days) |

**Примеры:**
- VRP_DEV → CLI и API пишут в один лист
- VRP_TEST → CLI и API пишут в один лист
- VRS_STAGE → CLI и API пишут в один лист

### PROD (критичные контуры)

| Тип проверки | Лист | Источник |
|--------------|------|----------|
| CLI | `GS_WORKSHEET_{ENV}` | Локальный Lighthouse |
| API | `GS_WORKSHEET_{ENV}` | PageSpeed API |
| CrUX | `GS_WORKSHEET_CHUX` | CrUX (28 days) |

**Примеры:**
- VRP_PROD → CLI и API пишут в один лист `VRP_PROD`
- VRS_PROD → CLI и API пишут в один лист `VRS_PROD`

---

## Структура строки

### Заголовки (CLI/API)

```
Date, Source, Iterations, Sprint, Env, Project, Route, Device,
P_p75,
LCP_p75, LCP_p90,
INP_p75, INP_p90,
CLS_p75, CLS_p90,
FCP_p75,
TBT_p75,
SI_p75,
TTI_p75,
TTFB_p75
```

### Пример строки

```
2026-03-19 11:45:00, CLI, 10, S24, PROD, VRP, home, desktop,
76,
1798, 2350,
88, 125,
0.0023, 0.0035,
1572,
210,
2450,
3200,
90
```

### Поле Source

| Значение | Описание |
|----------|----------|
| CLI | Локальный Lighthouse |
| API | PageSpeed API |

### Поле Iterations

Количество прогонов для агрегации:
- CLI: 10 (по умолчанию)
- API: 10 (по умолчанию)

---

## Различение результатов

В одном листе можно найти:
- Результаты CLI (Source=CLI)
- Результаты API (Source=API)

Для сравнения:
```sql
-- Пример фильтрации
SELECT * FROM sheet 
WHERE Env='PROD' AND Project='VRP' AND Route='home' AND Device='desktop'
ORDER BY Date DESC
```

---

## Настройка через .env

```ini
# VRP
GS_WORKSHEET_VRP_DEV=VRP [DEV]
GS_WORKSHEET_VRP_TEST=VRP [TEST]
GS_WORKSHEET_VRP_PROD=VRP [PROD]

# VRS
GS_WORKSHEET_VRS_DEV=VRS [DEV]
GS_WORKSHEET_VRS_STAGE=VRS [STAGE]
GS_WORKSHEET_VRS_PROD=VRS [PROD]

# CrUX (общий для всех)
GS_WORKSHEET_CHUX=CrUX Data
```

---

## Шаблоны

- `_CLI_Template` — шаблон для CLI/API листов
- `_API_Template` — то же (дублирует CLI)
- `_ChU_Template` — шаблон для CrUX