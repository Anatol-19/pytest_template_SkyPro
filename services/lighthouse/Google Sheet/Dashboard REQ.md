# PERFORMANCE QA DASHBOARD — REQUIREMENTS v2
## 🎯 0. ГЛАВНАЯ ЦЕЛЬ

#### Сделать dashboard, который:
- сам находит регрессии
- сам объясняет причины
- работает в 2 режимах:
  - Environment View (контур)
  - Sprint View (инкремент)
- даёт QA ответ:
  - 👉 “можно ли катить в прод и где риск”

---

## 🧠 1. ОСНОВНАЯ МОДЕЛЬ (ОБЯЗАТЕЛЬНО)

#### Все вычисления должны учитывать измерения:
- project (VRP / VRS)
- environment (DEV / TEST / STAGE / PROD)
- source (LAB / FIELD / API)
- device (mobile / desktop)
- page
- route_type
- run_id
- sprint
- tag (before / after / experiment)

---

## ⚠️ КРИТИЧНО

>❗ НЕЛЬЗЯ:
> - смешивать mobile и desktop
> - смешивать environments
> - сравнивать разные наборы страниц

---

## 🔴 2. BLOCK 0 — SMART ALERTS (ГЛАВНЫЙ БЛОК)

### 📌 Требование
Алерты должны быть:
- контекстные
- агрегированные
- actionable

---

### 📊 Формат:
```
[HIGH][PROD][mobile][category]
LCP regression +27% (6.3s → 8.1s)
Reason: TTFB 3.9s → backend bottleneck
```

---

### 🧮 Логика:

Сравнивать:
- Environment View → latest vs previous run
- Sprint View → before vs after

---

### 🚨 Правила
LCP
- +20% → HIGH
- +10% → MEDIUM
- +5% → LOW

INP
- 1000 ms → HIGH
- 200–1000 → MEDIUM

CLS
- 0.25 → HIGH
- 0.1 → MEDIUM
- std > 0.05 → MEDIUM

TTFB
- 800 ms → HIGH (backend)
- рост >20% → MEDIUM

---

### 🧠 Обязательная причина (root cause)

Каждый алерт должен объяснять:
- backend
- frontend
- SSR waterfall
- main thread
- layout shift

---

## 🟡 3. BLOCK — SMART DIAGNOSTICS (УЛУЧШЕННЫЙ)
### 📌 Rule Engine

Добавить:

**Backend**
`TTFB > 800`

**SSR waterfall**
`TTFB high AND LCP high`

**Frontend rendering**
`TTFB норм AND LCP > threshold`

**JS blocking**
`INP > 200 OR TBT > 300`

**Layout shift**
`CLS > 0.1 OR CLS std high`

**📊 Выход:**
```
Issue: SSR waterfall
Confidence: HIGH
Affected: mobile / category pages
```

---

## 🔵 4. BLOCK — OVERVIEW (КОНТЕКСТНЫЙ)
### 📌 Должен показывать:
- ТОЛЬКО выбранный срез:
  - project
  - environment
  - device
  - sprint

### ❗ Важно:
Если Device = ALL → показывать:
- mobile отдельно
- desktop отдельно

---

## 🟣 5. BLOCK — TREND (ПЕРЕДЕЛАТЬ)
### 📊 Обязательные элементы:
**Линии:**
- LCP p90
- INP p90
- CLS p90

**➕ Добавить:**
Sprint View:
- линия BEFORE
- линия AFTER

**❗ Требование:**
График должен отвечать:
- “стало лучше или хуже?”

---

## 🟢 6. BLOCK — CROSS-ENV COMPARISON
### 📊 Таблица:
```Env	Before	After	Δ	Status```

**📌 Используется в:**
- Sprint View
- Route Cross-Env

---

## 🔴 7. BLOCK — WORST PAGES
**📊 Требования:**
- top-10
- сортировка по LCP (mobile отдельно)

**➕ Добавить:**
- Δ (дельта)
- device

---

## 🟠 8. BLOCK — DEVICE SPLIT
**📊 Обязательно:**
- mobile vs desktop
- по текущему фильтру

**❗ правило:**
НЕ агрегировать их в одну цифру

---

## 🟤 9. BLOCK — ROUTE HEALTH (ПЕРЕДЕЛАТЬ)
**❌ Сейчас:**
- дубли
- нечитаемо

**✅ Нужно:**
Агрегация:
- page
- device
- environment

**Формат:**
```| Page | Device | LCP | Δ | Status | Reason |```

**Status:**
- BAD
- MEDIUM
- OK

---

## 🧪 10. BLOCK — SPRINT IMPACT (КЛЮЧЕВОЙ)
**📊 Таблица:**

```| Env | Device | Before | After | Δ | Result |```

**🧮 Логика:**
```
Δ < -10% → IMPROVED
Δ > +10% → REGRESSION
```
**❗ Обязательно:**
- mobile отдельно
- desktop отдельно

---

## 🧪 11. BLOCK — EXPERIMENTS
**📊 Таблица:**
```| Tag | Run | LCP | Δ | INP | CLS | Result |```

**📌 Логика:**
если есть tag:
→ сравнивать с baseline (без tag)

---

## 📉 12. BLOCK — STABILITY
**📊 Использовать:**
std deviation:
- LCP std
- INP std
- CLS std

**📌 Интерпретация:**
- высокий std = нестабильность
- даже если среднее ок → это проблема

---

## 📊 13. ГРАФИКИ (СТРОГО)
**1. Trend**
   - line chart
   - 3 линии
**2. Sprint Impact**
   - before vs after
   - по environment
**3. Device Split**
   - grouped bar
**4. Worst Pages**
   - bar chart

**❗ правило:**
1 график = 1 вопрос

---

## 🧱 14. FIXED LAYOUT ENGINE (КРИТИЧНО)
**📌 Нужно:**
жёстко задать координаты блоков:
```
BLOCK 0 → A1:F10
BLOCK 1 → A12:F20
BLOCK 2 → A22:J40
...
```

**➕ Charts zone:**
```
Trend → J2
Device → J20
```

**❗ запрещено:**
динамическое “расползание”

---

## ⚙️ 15. ТРИГГЕРЫ

**Обязательно:**
- onEdit → updatePerfAnalytics
- time-driven → каждые 2 часа

---

## 🧠 16. ПРАВИЛА АНАЛИТИКИ (САМОЕ ВАЖНОЕ)
**❗ 1. Никогда не сравнивать:**
- разные устройства
- разные страницы

**❗ 2. Sprint анализ = только before vs after**

**❗ 3. Environment анализ = latest vs previous**

**❗ 4. Всегда объяснять причину, а не просто цифру**

---

## 🧪 17. QA USE CASES (ОБЯЗАТЕЛЬНО ПОДДЕРЖАТЬ)

#### **Dashboard должен позволять:**

1. Проверка релиза
   - есть ли регресс в PROD
   - можно ли катить
2. Проверка спринта
   - стало лучше или хуже
   - на каких контурах
3. Debug
   - какая страница
   - какая причина
4. Core Web Vitals QA
   - LCP → backend vs frontend
   - INP → JS blocking
   - CLS → layout instability

---

## 🔥 18. КРИТЕРИЙ ГОТОВНОСТИ

**Dashboard считается готовым если:**

✅ за 30 секунд можно понять:
  - есть ли регресс
  - где он
  - почему он