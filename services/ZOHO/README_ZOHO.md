# ZOHO Projects — сервис и MCP-сервер

## Структура модуля

```
services/ZOHO/
├── Zoho_api_client.py   # HTTP-клиент Zoho Projects API (OAuth2)
├── mcp_server.py        # MCP-сервер — оборачивает клиента для Claude
├── User.py              # Модель пользователя + UserManager
├── TaskStatus.py        # Модель статуса задачи + TaskStatusManager
├── DefectStatus.py      # Модель статуса бага + DefectStatusManager
├── portal_data.py       # Предзаполненные данные команды и статусов
├── config_zoho.env      # Креды (gitignored: токены, client_id/secret)
└── README_ZOHO.md       # Этот файл
```

---

## ZohoAPI — что умеет

Файл: `Zoho_api_client.py`

Класс `ZohoAPI` — обёртка над Zoho Projects REST API v3.
Конфигурируется из `config_zoho.env`, автоматически обновляет access_token через refresh_token.

| Метод | Описание |
|-------|----------|
| `get_portals()` | Список порталов |
| `get_entities_by_filter(entity_type, ...)` | Задачи / баги / milestone'ы / таск-листы с фильтрами |
| `get_tasks_by_title(title)` | Поиск задач по названию таск-листа или milestone'а |
| `get_tasks_by_milestone(milestone_id)` | Задачи по milestone |
| `get_tasks_by_tasklist(tasklist_id)` | Задачи по таск-листу |
| `get_tasks_in_date_range(start, end)` | Задачи за период |
| `get_users(search_term)` | Список пользователей проекта |
| `get_milestone_id_by_name(name)` | ID milestone по названию |
| `get_tasklist_id_by_name(name)` | ID таск-листа по названию |
| `get_bug_statuses()` | Возможные статусы багов |
| `get_project_tags()` | Теги проекта |
| `manage_tag(tag_id, entity_id, entity_type, action)` | Привязка / отвязка тега |
| `create_bug(title, description, assignee_id, priority)` | Создание бага |
| `get_blueprint_graph()` | Граф Blueprint (статусы задач) |

### Конфигурация (`config_zoho.env`)

```
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...       # долгоживущий, обновляется автоматически
ZOHO_ACCESS_TOKEN=...        # перезаписывается при истечении
ZOHO_PORTAL_NAME=vrbgroup
ZOHO_PROJECT_ID=...
ZOHO_REGION=com              # com / eu / in / cn
```

Токены перезаписываются в файл автоматически через `save_tokens()`.

---

## MCP-сервер — что добавлено

Файл: `mcp_server.py`

FastMCP-сервер, который оборачивает `ZohoAPI` в протокол MCP (Model Context Protocol).
Позволяет Claude Code вызывать методы Zoho через инструменты (tools) напрямую в чате.

### Инструменты сервера

| Tool | Параметры | Описание |
|------|-----------|----------|
| `get_status` | — | Проверить подключение к API |
| `get_tasks` | `created_after`, `created_before`, `closed_after`, `closed_before`, `owner_name`, `milestone_name`, `tasklist_name`, `limit` | Задачи с фильтрами |
| `get_bugs` | `created_after`, `created_before`, `closed_after`, `closed_before`, `owner_name`, `limit` | Баги с фильтрами |
| `get_milestones` | — | Все milestone'ы |
| `get_tasklists` | — | Все таск-листы |
| `get_users` | `search` | Пользователи проекта |
| `get_tags` | — | Теги проекта |
| `create_bug` | `title`, `description`, `assignee_name`, `priority` | Создать баг |
| `get_tasks_by_title` | `title` | Задачи по имени таск-листа / milestone'а |
| `get_bug_statuses` | — | Возможные статусы багов |

### Запуск вручную

```bash
/Users/aqa/.hermes/hermes-agent/venv/bin/python services/ZOHO/mcp_server.py
```

Лог пишется в `Reports/zoho_mcp.log`.

### Регистрация в Claude Code

```bash
# Глобально (user scope) — доступен во всех чатах на этом компе:
claude mcp add zoho --scope user -- \
  /Users/aqa/.hermes/hermes-agent/venv/bin/python \
  /полный/путь/до/services/ZOHO/mcp_server.py

# Только для этого проекта:
claude mcp add zoho -- \
  /Users/aqa/.hermes/hermes-agent/venv/bin/python \
  /Users/aqa/PycharmProjects/pytest_template_SkyPro/services/ZOHO/mcp_server.py
```

### Перенос на другой компьютер

1. Скопируй проект (или только `services/ZOHO/`)
2. Убедись что в venv установлен пакет `mcp`: `pip install mcp`
3. Убедись что установлены `requests` и `python-dotenv`
4. Зарегистрируй сервер командой выше (с актуальным путём к python и проекту)
5. Обнови токены в `config_zoho.env` если они истекли

---

## Связанные модули

- `services/Release_Test_Plan/TestPlanGenerator.py` — генератор QA-планов, использует `ZohoAPI`
- `test/test_zoho.py` — тесты клиента (исключены из `pytest.ini`, запускать вручную)
- `portal_data.py` — предзаполненные данные команды и статусов (не требует вызова API)
