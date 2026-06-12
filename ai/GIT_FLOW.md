# Git Flow — регламент для pytest_template_SkyPro

> Обязателен для обеих машин (macOS + Windows).
> Договорено: 2026-06-12.

---

## Принцип

Работа в `main` напрямую **запрещена** (кроме мелких hotfix-правок документации).
Каждый логический инкремент — отдельная ветка. Ветка мержится в `main` только когда
инкремент завершён и работоспособен.

---

## Именование веток

```
<type>/<kebab-case-description>
```

| Тип | Когда использовать | Пример |
|---|---|---|
| `feat/` | новая функциональность | `feat/payment-centrobill` |
| `fix/` | исправление бага | `fix/bundle-crosssale-member-id` |
| `chore/` | инфраструктура, конфиги, документация | `chore/mcp-zoho-windows` |
| `epic/` | крупная фаза (несколько под-задач) | `epic/payment-phase2-epoch-extras` |
| `refactor/` | рефакторинг без изменения поведения | `refactor/payment-flow-cleanup` |

**Правила:**
- Только строчные буквы, дефис как разделитель
- Описание — ёмкое, 2–4 слова
- Не использовать номера задач в названии (нет единого трекера)

---

## Цикл работы

### Начало инкремента

```bash
git checkout main
git pull origin main
git checkout -b feat/my-feature
```

### В процессе работы

```bash
# Коммит после каждой логической единицы (не накапливать)
git add <files>
git commit -m "feat: описание что сделано"
```

Правила коммит-сообщений (уже соблюдаются в проекте):
- `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Первая строка — краткая (до 72 символов)
- Тело — при необходимости, объяснение ПОЧЕМУ

### Завершение инкремента

```bash
git checkout main
git pull origin main          # на случай если другая машина что-то добавила
git merge --no-ff feat/my-feature
git push origin main
git branch -d feat/my-feature
```

`--no-ff` сохраняет историю ветки в графе.

---

## Работа с двух машин

### Правило одной ветки

**Только одна машина работает с одной веткой одновременно.**
Не переключаться между компьютерами пока ветка не смержена.

### Если нужно переключиться между машинами не завершив инкремент

```bash
# На текущей машине — сохранить прогресс
git push origin feat/my-feature          # push ветки на remote

# На другой машине — продолжить
git fetch origin
git checkout feat/my-feature
```

### Синхронизация в начале каждой сессии

```bash
git pull origin main           # если работаешь с main
# или
git pull origin feat/my-feature  # если продолжаешь ветку
```

---

## Планируемые инкременты (бэклог)

Соответствует `ai/PAYMENT_EXPANSION_PLAN.md`:

| Ветка | Содержание |
|---|---|
| `epic/payment-phase2-epoch-extras` | Chargeback(D), CrossSale, Slave-сторона бандла |
| `feat/payment-centrobill` | Centrobill разовые платежи |
| `feat/payment-sale-events` | Sale Events + Layer 01 Tariffs + re-join |
| `feat/zoho-mcp-skills` | Zoho MCP скиллы в Claude Code |
| `chore/postman-sync` | Синхронизация Postman-коллекции с Python-реализацией |

---

## Что НЕ коммитить (напоминание)

- `.env`, `config_zoho.env`, `config_lighthouse.env` — credentials gitignored
- `Reports/` — отчёты gitignored
- `.idea/` — IDE-настройки gitignored
- `tools/verify_arp_playa_assets.py` — не трогать до явного решения
