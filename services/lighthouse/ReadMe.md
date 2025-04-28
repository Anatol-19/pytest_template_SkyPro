# 📈 Lighthouse Automation Service
> Автономный сервис для автоматизированного тестирования производительности, доступности, лучших практик и SEO веб-страниц через Lighthouse CLI, Google PageSpeed API и Chrome UX Report (CrUX).

### 📌 Основные возможности
- 3 типа тестов:
  - CLI запуск: Агрегация метрик из N итераций локального Lighthouse CLI.
  - API запуск: Агрегация базовых Core Web Vitals через Google PageSpeed Insights API.
  - CrUX сбор данных: Сбор реальных пользовательских метрик за последние 28 дней через CrUX API.
- Параметризация запусков:
  - Количество итераций
  - Список роутов
  - Тип устройства (desktop/mobile)
  - Эмуляция сетевых условий и юзер-агентов
  - Выбор категорий Lighthouse: Performance, Accessibility, Best Practices, SEO
  - Поддержка режимов Lighthouse: Navigation / Snapshot / Timespan
- Интеграция с Google Sheets:
    - Автоматическая запись результатов в таблицы.
    - Автопоиск или создание вкладки по шаблонам в зависимости от типа теста и окружения.
- Автономность и готовность к интеграции:
  - Работает как отдельный сервис или встраивается в существующие тестовые фреймворки.
  - Полностью настраивается через .env, .ini и .json файлы.
  - Поддержка Pytest-параметризации для дальнейшего масштабирования тестов.

    

### Структура и автономность
1. #### Структура
 └─── /lighthouse/                  # Основная логика работы с Lighthouse
│       └── configs/                   # 
│           ├── config_lighthouse.py   # 📌 Чтение настроек из config.ini
│           └── Файлы ini и JSON       # 📌
│       └── creds/                     # JSON  доступами к API Гугла для сохранения результатов
│       ├── __init__.py                # Делает пакет импортируемым
│       ├── cli_runner.py              # 📌 Lighthouse CLI
│       ├── api_runner.py              # 📌 Google Lighthouse API
│       ├── processor_lighthouse.py    # 📌 Парсинг и обработка результатов (ОБЩИЙ для локального и удалённого)
│       ├── cleaner.py                 # 📌 Очистка временных файлов
│       └── speedtest_service.py       # 📌 Главный сервис (запускает CLI/API + обработку)

│── Reports/                           # CSV файлы с результатами тестов
│   └── reports_lighthouse/            # Отчёты от Lighthouse
│       └── temp_lighthouse/           # Временные файлы от Lighthouse


2. #### Централизованное управление путями
    Все пути для отчетов и временных файлов должны управляться в config_lighthouse.py. Это включает:
    Пути для отчетов (REPORTS_DIR).
    Пути для временных файлов (TEMP_REPORTS_DIR).
    Пути для ChUX отчетов (CHUX_REPORTS_DIR).
    ⚙️ Конфигурация:
    - config_lighthouse.env — переменные окружения (ключи API, ID таблиц Google Sheets)
    - routes.ini — список тестируемых роутов
    - config_desktop.json, config_mobile.json — настройки устройств (разрешение, сеть, UA)
    - base_urls.ini — описание окружений (DEV, TEST, PROD)

    Пути для отчетов централизованы в config_lighthouse.py:
    ```
   # config_lighthouse.py
   ROOT_DIR = Path(__file__).resolve().parents[2]  # Корневая директория проекта
   REPORTS_DIR = ROOT_DIR / "Reports" / "reports_lighthouse"  # Основные отчеты
   TEMP_REPORTS_DIR = REPORTS_DIR / "temp_lighthouse"  # Временные файлы
   CHUX_REPORTS_DIR = REPORTS_DIR / "chux_reports"  # Отчеты ChUX
   
   def ensure_directories_exist():
        """Создает все необходимые директории."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        CHUX_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


3. #### Автономность
Сервис должен быть автономным, но готовым к интеграции. Для этого:
Все зависимости (например, Google Sheets, Lighthouse CLI) должны быть проверены при инициализации.
Конфигурация (пути, ключи API) должна загружаться из файлов .env или config.ini.
 
2. Поддержка ChUX метрик
2.1. Добавление ChUX метрик
ChUX метрики включают:
Core Web Vitals (LCP, FID, CLS).
Дополнительные метрики (TBT, SI, TTI).
Данные за 28 дней (агрегированные значения).
3. Интеграция в тестовый фреймворк
3.1. Параметризация
Сервис должен поддерживать параметризацию:
Роуты: Список URL для тестирования.
Тип устройства: desktop или mobile.
Количество итераций: Для CLI тестов.
Частота запуска: Для ChUX тестов (например, раз в 14 дней).

 
4. Интеграция с Google Sheets
4.1. Шаблоны для отчетов
Создадим отдельные шаблоны для:
CLI отчетов.
API отчетов.
ChUX отчетов.

