# Точка входа для ИИ-агента (Claude Code)

> Читай этот файл первым при старте новой сессии в этом проекте.
> Здесь — суть проекта, ссылки на детали и правила порядка.

---

## Что это за проект

QA-фреймворк автоматизации для платформ **VRPorn** и **VRSmash**.
Язык: Python 3.12. Фреймворк: Pytest + Allure. Все комментарии, логи, docstrings — **по-русски**.

Три независимых направления:

| Направление | Тест | Инструменты |
|---|---|---|
| Функциональные / GUI | `test/simple_test.py` | Selenium + POM |
| Производительность | `test/speed_test.py` | Lighthouse CLI / PageSpeed API |
| Content Assets (API) | `test/test_content_assets.py` | Requests |
| Payment (API) | `test/test_payment.py` | Requests + Epoch + Segpay |

---

## Как запускать

```bash
# Установить зависимости
pip install -r requirements.txt

# Payment-тесты (основная активная работа)
.venv/bin/python -m pytest -m payment --environment=VRP_STAGE -v

# Все команды payment — ai/PAYMENT_RUN_COMMANDS.md
# Allure
bash tools/allure_report.sh
```

---

## Критически важные файлы

| Файл | Зачем |
|---|---|
| `CLAUDE.md` | Главная инструкция для Claude Code |
| `URLs/base_urls.ini` | Все окружения. НЕ менять `current` вручную |
| `URLs/routes.ini` | Именованные маршруты |
| `REST/base_client.py` | Ядро HTTP-клиента |
| `services/payment/config_payment.py` | Константы + **SALE_EVENT_KEYS** (DropCard конфиг) |
| `services/payment/payment_flow.py` | Оркестратор сценариев |
| `services/payment/epoch_payloads.py` | Тела Epoch-постбэков |
| `services/payment/segpay_payloads.py` | Тела Segpay-постбэков |
| `test/conftest.py` | Фикстуры + CLI-флаги |

---

## Документы ai/

| Файл | Содержание |
|---|---|
| `CONTEXT_TRANSFER.md` | **Этот файл — точка входа** |
| `VRP_BUSINESS_LOGIC.md` | Авторитетная бизнес-логика (из Docmost) |
| `VRP_PAYMENT_TESTING.md` | Детали платёжного тестирования |
| `PAYMENT_CASES_MATRIX.md` | Утверждённые 11 кейсов |
| `PAYMENT_EXPANSION_PLAN.md` | Фазы 1-4: Segpay/Centrobill/Epoch-extras/Sale Events |
| `PAYMENT_RUN_COMMANDS.md` | Команды запуска, Allure |
| `POSTMAN_ANALYSIS.md` | Анализ Postman-коллекции |
| `PROJECT_REPORT.md` | Архитектурный снимок проекта |

---

## Ключевые архитектурные решения (не менять без обсуждения)

- `BaseApiClient` читает роуты из `routes.ini`, не хардкодит URL
- ConfigParser → все ключи нижним регистром: `base_url`, не `BASE_URL`
- **Не писать** в `base_urls.ini[environments] current` — только `--environment=` флаг
- Epoch: FlexPost[M] JSON + DataPlus form-urlencoded через `/api/payment/sync-handler/epoch`
- Segpay: один form-постбэк на событие через `/api/payment/sync-handler/segpay`; ответ — строка `"OK"`
- **CrossSale ≠ Bundle**: CrossSale — DataPlus без инвойса (инициирует платёжка, мы не создавали invoice); Bundle — Dynamic Price, мы slave, нет инвойса
- Все бандл/самосепарат постбэки (FlexPost И DataPlus) ОБЯЗАНЫ содержать `x_invoice` + `x_bundle_*`, иначе бэкенд создаёт CrossSale-мембершип
- DropCard sale event ключи по контурам — `config_payment.SALE_EVENT_KEYS`; тест пропускается если ключ не настроен

---

## Правила порядка в проекте (регламент)

### При начале сессии
1. Прочитай этот файл + `CLAUDE.md`
2. Если задача по payment — открой `VRP_BUSINESS_LOGIC.md` и `PAYMENT_CASES_MATRIX.md`
3. Проверь `git status` — не оставляй незакоммиченных изменений по завершении

### Что коммитить
- Каждая логическая единица — отдельный коммит с описательным сообщением
- `.idea/`, `*.pyc`, `Reports/`, `.env` — не коммитить (см. `.gitignore`)
- `tools/verify_arp_playa_assets.py` — не трогать до явного решения по нему

### Документы ai/
- `ai/` — для людей и агентов: бизнес-логика, планы, матрицы кейсов
- Не хранить в `ai/` per-contour runtime-конфиги → они в `config_payment.py`
- Удалять устаревшие доки сразу (не накапливать `*_v2.md`, `*_old.md`)
- Перед удалением дока — убедись что его содержание отражено в актуальном файле

### Для агента на другом компьютере
При первом запуске после `git pull`:
1. Прочитай этот файл
2. Проверь `git log --oneline -5` — убедись что на актуальном коммите
3. Если есть незакоммиченные изменения — разберись что это (`git diff`) до работы
4. Запусти `pytest --collect-only -m payment` — проверь что всё импортируется
5. Следуй `CLAUDE.md` и этому файлу

---

## Текущий статус (обновлять при смене фазы)

**Активная работа:** Payment-тесты, Фаза 1 (Epoch + Segpay) — в процессе  
**Следующая фаза:** Epoch extras (Chargeback/CrossSale/Slave-side) → Centrobill → Sale Events  
**Известные ограничения:** Segpay upgrade синтетически не воспроизводится (живой API)  
**На VRP_PROD:** настроен только DropCard SS; остальные ключи только на тестовых контурах
