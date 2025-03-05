# pytest_template_SkyPro

## Шаблон для автоматизации тестирования на python

### Шаги
1. Склонировать проект 'git clone https://github.com/имя_пользователя/
   pytest_ui_api_template.git'
2. Установить зависимости
3. Запустить тесты 'pytest'

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
- ./test - тесты
- ./pages - описание страниц
- ./api - хелперы для работы с API
- ./db - хелперы для работы с БД

/pytest_framework                  
│── /data/                        # CSV файлы с результатами тестов
│── POM/                          # Page Object Model (не изменяем)
│── REST/                         # REST API (не изменяем)
│── /test/                        # PyTest тесты
│   └── test_speed.py             # Тесты на скорость (вызывают сервис)
│── /utils/                       # Вспомогательные утилиты (не изменяем)
│── /lighthouse/                  # Основная логика работы с Lighthouse
│   ├── __init__.py               # Делает пакет импортируемым
│   ├── cli_runner.py             # 📌 Запуск Lighthouse CLI (локальный)
│   ├── api_runner.py             # 📌 Google Lighthouse API (будет добавлен позже)
│   ├── processor_lighthouse.py   # 📌 Парсинг и обработка результатов (ОБЩИЙ)
│   ├── cleaner.py                # 📌 Очистка временных файлов
│   ├── config_lighthouse.py      # 📌 Чтение настроек из config.ini
│   ├── speedtest_service.py      # 📌 Главный сервис (запускает CLI/API + обработку)
│   ├── reports/                  # Временные файлы от Lighthouse
│── config.ini                    # 📌 Конфигурация проекта
│── requirements.txt              # Зависимости проекта
│── README.md                     # Документация
│── .gitignore                    # Исключаем ненужные файлы


### Полезные ссылки
- [Подсказка по markdown](https://www.markdownguide.org/basic-syntax/)
- [Генератор файла gitignore](https://www.toptal.com/developers/gitignore)

### Библиотеки (!)
- `pip install pytest`
- `pip install selenium`
- `pip install webdriver-manager`
- numpy