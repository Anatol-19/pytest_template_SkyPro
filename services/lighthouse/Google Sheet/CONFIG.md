# Config Sheet — Руководство по настройке

## 📋 Назначение

Лист **`Config`** в Google Sheets — это **единая точка конфигурации** для:
- Порогов метрик (good/poor)
- Списка страниц для мониторинга
- Настроек дашборда

---

## 🔧 1. Пороги метрик (Metric Thresholds)

### Структура таблицы:

| metric | good | poor | direction |
|--------|------|------|-----------|
| lcp | 2500 | 4000 | low_good |
| inp | 120 | 500 | low_good |
| cls | 0.12 | 0.25 | low_good |
| ttfb | 800 | 1800 | low_good |
| fcp | 1800 | 3000 | low_good |
| tbt | 300 | 600 | low_good |
| tti | 3800 | 7300 | low_good |
| speed | 3400 | 5800 | low_good |
| p | 90 | 50 | high_good |

### 📌 Правила:

| Поле | Описание | Пример |
|------|----------|--------|
| `metric` | Имя метрики (строчные буквы, подчёркивания) | `lcp`, `inp`, `cls` |
| `good` | Порог "хорошего" значения | `2500` (мс) |
| `poor` | Порог "плохого" значения | `4000` (мс) |
| `direction` | Направление оценки | `low_good` или `high_good` |

### 🧭 Direction:

| Значение | Описание | Пример |
|----------|----------|--------|
| `low_good` | **Меньше = лучше** (время, задержки) | LCP, INP, TTFB |
| `high_good` | **Больше = лучше** (проценты, очки) | Performance Score (`p`) |

---

## 📄 2. Страницы (Routes)

### ⚡ Важно:

**Страницы НЕ нужно добавлять в Config!** 

Система **автоматически обрабатывает все страницы**, которые есть в raw-листах:
- `VRP [PROD]`, `VRP [STAGE]`, `VRP [TEST]`, `VRP [DEV]`
- `VRS [PROD]`, `VRS [STAGE]`, `VRS [TEST]`, `VRS [DEV]`
- `CrUX`

### 🔄 Как добавить новую страницу:

1. **Просто начни собирать данные** для новой страницы в raw-листы
2. При следующем запуске `updatePerfAnalytics()`:
   - Страница автоматически появится в `Routes` sheet
   - Будет обрабатываться в дашборде
   - Появится в фильтрах и алертах

### 📊 Пример raw-данных:

| date | run_id | page | device | lcp | inp | cls | ... |
|------|--------|------|--------|-----|-----|-----|-----|
| 2026-03-30 | run_123 | **new_page** | mobile | 2100 | 95 | 0.08 | ... |

→ Страница `new_page` автоматически появится в дашборде!

---

## 🎨 3. Цвета статусов

| Статус | Цвет (hex) | Когда |
|--------|------------|-------|
| GOOD | `#C8E6C9` | Метрика в зелёной зоне |
| NI (Needs Improvement) | `#FFF9C4` | Метрика между good и poor |
| POOR | `#FFCDD2` | Метрика хуже poor |

---

## 🧩 4. Маппинг типов страниц

Автоматический маппинг имён страниц в типы (для группировки):

| Имя страницы | Тип |
|--------------|-----|
| `main` | `home` |
| `s_video`, `models`, `s_model` | `model` |
| `categories`, `s_category` | `category` |
| `s_studio` | `studio` |
| `dreams`, `s_dream` | `content` |

Чтобы добавить свой маппинг — измени `ROUTE_TYPE_MAP` в `00_Constants.gs`.

---

## 🛠 5. Как редактировать Config

### Шаг 1: Открой Google Sheet

1. Открой свою Performance QA Dashboard Google Sheet
2. Перейди на лист **`Config`**

### Шаг 2: Добавь/измени метрику

| Действие | Как |
|----------|-----|
| Изменить порог LCP | Найди строку `lcp`, измени `good` или `poor` |
| Добавить метрику | Добавь новую строку: `metric`, `good`, `poor`, `direction` |
| Удалить метрику | Удали строку (останется fallback из кода) |

### Шаг 3: Сохрани

Config применяется **автоматически** при следующем запуске:
- Меню **QA Dashboard → Generate Dashboard**
- Или кнопка **Generate Dashboard**

---

## 🚨 6. Fallback (резервные пороги)

Если Config sheet **не найден** или **пуст**, система использует пороги из кода:

```javascript
// 00_Constants.gs — DEFAULT_METRIC_FALLBACKS
{ metric: 'lcp', good: 2500, poor: 4000, direction: 'low_good' }
{ metric: 'inp', good: 120, poor: 500, direction: 'low_good' }
{ metric: 'cls', good: 0.12, poor: 0.25, direction: 'low_good' }
// ... и другие
```

---

## 📈 7. Примеры использования

### 🔴 Пример 1: Ужесточить пороги LCP

Хотим, чтобы LCP был ≤ 2000ms (вместо 2500ms):

| metric | good | poor | direction |
|--------|------|------|-----------|
| lcp | **2000** | **3000** | low_good |

### 🟡 Пример 2: Добавить новую метрику FID

| metric | good | poor | direction |
|--------|------|------|-----------|
| fid | 100 | 300 | low_good |

### 🟢 Пример 3: Изменить направление для Score

| metric | good | poor | direction |
|--------|------|------|-----------|
| p | 95 | 70 | **high_good** |

---

## ❓ FAQ

### Q: Как добавить новую страницу?
**A:** Не нужно добавлять в Config! Просто начни писать данные для страницы в raw-листы.

### Q: Config не применяется?
**A:** Проверь:
1. Лист называется точно **`Config`** (с большой буквы)
2. Заголовки: `metric`, `good`, `poor`, `direction`
3. Запусти **Generate Dashboard** заново

### Q: Можно ли удалить метрику из Config?
**A:** Да, но для неё будет использоваться fallback из кода.

### Q: Как добавить свой цвет статуса?
**A:** Измени `STATUS_COLORS` в `00_Constants.gs`.

---

## 📎 Приложения

### A. Полный список метрик

| Метрика | Описание | Единица | Direction |
|---------|----------|---------|-----------|
| `lcp` | Largest Contentful Paint | ms | low_good |
| `inp` | Interaction to Next Paint | ms | low_good |
| `cls` | Cumulative Layout Shift | — | low_good |
| `ttfb` | Time to First Byte | ms | low_good |
| `fcp` | First Contentful Paint | ms | low_good |
| `tbt` | Total Blocking Time | ms | low_good |
| `tti` | Time to Interactive | ms | low_good |
| `speed` | Speed Index | ms | low_good |
| `p` | Performance Score | % | high_good |

### B. Ссылки

- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse Metrics](https://developer.chrome.com/docs/lighthouse/overview/)

---

**Последнее обновление:** 2026-03-30  
**Версия:** 1.0
