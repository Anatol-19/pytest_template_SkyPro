# pytest_template_SkyPro

## Шаблон для автоматизации тестирования на python

### Шаги
1. Склонировать проект 'git clone "Pytest Template""'
2. Установить зависимости
   - _Create a virtual environment:_
     - `python -m venv .venv`
            или
     - `py -m venv .venv`
   - _Activate the virtual environment:_
     - On Windows `.venv\Scripts\activate`
     - On macOS/Linux `source .venv/bin/activate`
   - `pip install -r requirements.txt`
3. Запуск готовых сценариев (CLI из корня)
   - PROD full (VRP_PROD, все роуты, CLI+API, 5 итераций): `python run_prod_full.py`
   - PROD main + CrUX оба проекта: `python run_prod_crux.py`
   - PROD main оба проекта CLI+API: `python run_prod_tests.py`
   - STAGE+TEST все роуты CLI: `python run_stage_test.py`
   - Если нужен прямой вызов сервиса: импортируйте `SpeedtestService(environment="VRP_PROD")`
     и вызывайте `run_local_tests`, `run_api_aggregated_tests`, `run_crux_data_collection`.
   - Для параллельных запусков задавайте `environment` в конструкторе (не требуется менять base_urls.ini).

### MCP/Agent API (для внешнего агента)
- Запуск MCP: `python services/lighthouse/mcp_server.py`
- Доступные инструменты (FastMCP):
  - `enqueue_lighthouse(routes, device, iterations=5, environment=None)` → возвращает `job_id`, запускает Lighthouse CLI в фоне.
  - `enqueue_crux(routes, device, environment=None)` → CrUX сбор в фоне.
  - `list_jobs()` → статусы всех заданий (queued/running/done/error).
  - `job_status(job_id)` → статус конкретного задания.
  - Вспомогательные: `run_lighthouse`, `run_crux` (синхронные), `list_environments`, `list_routes`, `get_status`.
- Параллельность: задания не трогают `base_urls.ini`, каждый `SpeedtestService` получает `environment` напрямую, поэтому несколько фоновых процессов не конфликтуют.

### Стек:
- Pytest
- Selenium
- Requests
- _Sqlalchemy_
- Allure
- config
- Faker
- SpeedTest
- Perfect Pixel

### Струткура:
```mermaid
/pytest_framework                  
│── ./data/                            # CSV файлы с результатами тестов
│── Reports/                           # CSV файлы с результатами тестов
│   └── reports_lighthouse/            # Отчёты от Lighthouse
│       └── temp_lighthouse/           # Временные файлы от Lighthouse
│── ./POM/                             # Page Object Model
│── ./REST/                            # REST API - хелперы для работы с API
│── ./db/                              # хелперы для работы с БД
│── ./test/                            # PyTest тесты
│    test_speed.py                     # Тесты на скорость (вызывают сервис lighthouse)
│   ├── test_speed.py                  # Тесты на скорость (вызывают сервис lighthouse)
│   └── conftest.py                    # Конфигурация PyTest
│── ./utils/                           # Вспомогательные утилиты
│── /services/                         # Сервисы выполненные самостоятельными модулями
│   └── ./google/                      # Google API
│       ├── google_sheets_client.py    # Взаимодействие с таблицами и Гугл док
│   └─── /lighthouse/                  # Основная логика работы с Lighthouse
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
│── config.ini                         # 📌 Конфигурация проекта
│── requirements.txt                   # Зависимости проекта
│── README.md                          # Документация
└── .gitignore                         # Исключаем ненужные файлы
```

### Полезные ссылки
- [Подсказка по markdown](https://www.markdownguide.org/basic-syntax/)
- [Генератор файла gitignore](https://www.toptal.com/developers/gitignore)

### Библиотеки (!)
- `pip install pytest`
- `pip install selenium`
- `pip install webdriver-manager`
- numpy



## Реализация флагов для конфигурации тестов

В этом проекте реализована система флагов, которая позволяет настраивать параметры запуска тестов через командную строку. Это обеспечивает гибкость и удобство при запуске тестов в различных окружениях (локально или в Docker).

### Глобальные переменные

Глобальные переменные, используемые для конфигурации тестов, объявлены в файле `config.py`. Эти переменные инициализируются в зависимости от переданных флагов при запуске тестов.

### Доступные флаги

При запуске тестов с помощью `pytest` вы можете использовать следующие флаги:

- `--browser`: Указывает тип браузера, который будет использоваться для тестирования. Доступные значения:
  - `chrome`
  - `firefox`
  - `opera`
  - `edge`
  
  **По умолчанию**: `chrome`

- `--browser-version`: Указывает версию браузера, которая будет использоваться. Если не указана, будет использована последняя доступная версия для локального запуска или "latest" для Docker.

- `--headless`: Запускает браузер в безголовом режиме. Этот флаг не требует значения и используется как переключатель.

- `--screen-resolution`: Указывает разрешение экрана, которое будет использоваться при запуске браузера. Например, `1920x1080`.

  **По умолчанию**: `1920x1080`

- `--user-agent`: Указывает строку User-Agent, которая будет использоваться при тестировании. 

  **По умолчанию**: `Mozilla/5.0`

- `--local`: Указывает, что тесты запускаются локально. Этот флаг не требует значения и используется как переключатель.

- `--docker`: Указывает, что тесты запускаются в Docker. Этот флаг не требует значения и используется как переключатель.

- `--contour`: Указывает контур тестирования. Например, `development`, `staging`, `production`.

  **По умолчанию**: `development`

- `--test-flags`: Позволяет указать дополнительные флаги для тестов в виде запятой, например, `flag1,flag2`.

### Примеры запуска тестов

1. Запуск тестов локально с использованием Chrome в безголовом режиме:
   ```bash
   pytest --browser=chrome --headless --screen-resolution=1920x1080 --user-agent="Mozilla/5.0" --local
   ```
2. Запуск тестов в Docker с использованием Firefox:
   ```bash
   pytest --browser=firefox --headless --docker
   ```
### Логика выбора версии браузера

При запуске тестов локально, если не указана версия браузера, система автоматически определяет установленную версию браузера. Если тесты запускаются в Docker, используется значение "latest" или конкретная версия, если она указана.
