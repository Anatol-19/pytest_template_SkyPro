# Метрики Lighthouse CLI — Спецификация

## Три метода тестирования

### 1. CrUX (field data)
**Источник:** PageSpeed API → `loadingExperience`
**Агрегация:** Готовые перцентили от Google (28 дней)

| Метрика | Формат | Примечание |
|---------|--------|------------|
| LCP_p75 | ms (целые) | 75-й перцентиль |
| FCP_p75 | ms (целые) | 75-й перцентиль |
| INP_p75 | ms (целые) | 75-й перцентиль |
| CLS_p75 | score × 100 | 75-й перцентиль |
| LCP_good_% | % (1 знак) | % пользователей в зелёной зоне |
| FCP_good_% | % (1 знак) | Аналогично |
| INP_good_% | % (1 знак) | Аналогично |
| CLS_good_% | % (1 знак) | Аналогично |
| TTFB | ms (целые) | Percentile |

### 2. CLI Navigation (lab data)
**Источник:** Lighthouse CLI → `lighthouseResult.audits`
**Режим:** `--mode=navigation` (по умолчанию)
**Итерации:** N прогонов (по умолчанию 10)

| Метрика | Тип | Агрегация | Формат |
|---------|-----|-----------|--------|
| **LCP** | Core Web Vitals | p75, p90 | ms (целые) |
| **INP** | Core Web Vitals | p75, p90 | ms (целые) — timespan |
| **CLS** | Core Web Vitals | p75, p90 | score (4 знака) |
| P | Performance | p75 | score 0-100 |
| FCP | Performance | p75 | ms (целые) |
| TBT | Performance | p75 | ms (целые) |
| SI | Performance | p75 | ms (целые) |
| TTI | Performance | p75 | ms (целые) |
| TTFB | Performance | p75 | ms (целые) |

### 3. CLI Timespan (INP)
**Источник:** Lighthouse CLI + Puppeteer → `timespan mode`
**Режим:** `--mode=timespan`
**Итерации:** N прогонов (по умолчанию 5)

| Метрика | Агрегация | Формат |
|---------|-----------|--------|
| INP | p75, p90 | ms (целые) |

**Примечание:** Timespan запускается отдельно для измерения INP.

---

## Методы агрегации

### Core Web Vitals (LCP, INP, CLS)
- **p75** — типичное значение (75% пользователей)
- **p90** — худший случай (проблемы)

### Остальные метрики (P, FCP, TBT, SI, TTI, TTFB)
- **p75** — достаточно для анализа

### Удалено
- ~~min~~ — оптимистичный, не нужен
- ~~max~~ — хуже p90
- ~~avg~~ — искажается выбросами

---

## Округление

| Метрика | Округление | Пример |
|---------|------------|--------|
| ms (LCP, FCP, TBT, SI, TTI, TTFB, INP) | целые | 1798 |
| score (CLS) | 4 знака | 0.0023 |
| % (good_%) | 1 знак | 78.5 |
| P (performance) | целые | 76 |

---

## Структура таблицы CLI

### Заголовки

```
Date, RunID, Sprint, Env, Project, Route, Device,
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
2026-03-19, 20260319_0930, S24, PROD, VRP, home, desktop,
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

---

## Запуск тестов

### Navigation (основные метрики)
```bash
lighthouse <url> --mode=navigation --output=json
```

### Timespan (INP)
```bash
node scripts/lighthouse_inp.js <url> desktop
```

### Итерации
- Navigation: 10 прогонов
- Timespan: 5 прогонов (медленнее)

---

## Интеграция

```python
# CLI navigation
run_local_lighthouse(url, iterations=10, mode="navigation")

# CLI timespan (INP)
run_inp_test(url, device="desktop", iterations=5)
```

---

## CrUX vs CLI

| Метрика | CrUX (field) | CLI (lab) |
|---------|--------------|-----------|
| LCP | p75, good_% | p75, p90 |
| FCP | p75, good_% | p75 |
| INP | p75, good_% | p75, p90 (timespan) |
| CLS | p75, good_% | p75, p90 |
| TBT | — | p75 |
| SI | — | p75 |
| TTI | — | p75 |
| TTFB | percentile | p75 |
| P | — | p75 |