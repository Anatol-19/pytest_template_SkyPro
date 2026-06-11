# MCP Setup Status

Этот файл описывает состояние MCP-интеграций на момент последнего коммита.
Обновляется вручную при переносе между машинами.

---

## Что сделано

### Zoho Projects MCP (`services/ZOHO/mcp_server.py`)

**Статус: код готов, требует проверки токенов на целевой машине**

- FastMCP-сервер написан поверх существующего `ZohoAPI`
- Регистрируется командой:
  ```bash
  claude mcp add zoho --scope user -- \
    <путь_к_python_с_пакетом_mcp> \
    <абс_путь>/services/ZOHO/mcp_server.py
  ```
- На macOS с Claude Code Desktop python берётся из:
  `/Users/<user>/.hermes/hermes-agent/venv/bin/python`
- Пакет `mcp` должен быть установлен: `pip install mcp`

**Проблема на машине разработки (MacBook Air M-chip):**
- `get_portals()` вернул пустой ответ — вероятно истёк `ZOHO_ACCESS_TOKEN`
- `ZOHO_REFRESH_TOKEN` в `config_zoho.env` должен обновить его автоматически,
  но на новой машине это не сработало с первого запуска
- **Что проверить на основной машине:**
  1. Убедиться что `ZOHO_REFRESH_TOKEN` в `config_zoho.env` актуален
  2. Запустить `python services/ZOHO/mcp_server.py` вручную и проверить лог:
     `Reports/zoho_mcp.log`
  3. Если токен протух — получить новый через Zoho Developer Console

---

### Lighthouse MCP (`services/lighthouse/mcp_server.py`)

**Статус: код готов, отсутствует файл Google credentials**

- FastMCP-сервер существовал, но не был нигде зарегистрирован — исправлено
- Регистрируется аналогично Zoho:
  ```bash
  claude mcp add lighthouse --scope user -- \
    <путь_к_python_с_пакетом_mcp> \
    <абс_путь>/services/lighthouse/mcp_server.py
  ```
- Lighthouse CLI установлен, работает
- GS_SHEET_ID задан в `config_lighthouse.env`

**Проблема: отсутствует файл Google Service Account credentials**
- Ожидаемый путь (из `config_lighthouse.env`):
  `services/lighthouse/creds/voluptas-488008-e88abce2f685.json`
- Папка `creds/` не существует в репозитории (gitignored — правильно)
- Файл находится на основной рабочей машине
- **Что сделать на основной машине:**
  1. Создать папку `services/lighthouse/creds/`
  2. Скопировать туда `voluptas-488008-e88abce2f685.json`
  3. Убедиться что путь в `config_lighthouse.env` совпадает: `GS_CREDS=services/lighthouse/creds/voluptas-488008-e88abce2f685.json`

---

### Docmost MCP

**Статус: работает на обеих машинах**

- Установлен глобально, регистрация через `claude mcp add`
- Исходники: `~/.claude/mcp-servers/docmost-mcp/` (не в этом репо)
- При переносе на новую машину — клонировать и собрать отдельно

---

### Qase MCP

**Статус: работает на обеих машинах**

- Запускается через `npx @qase/mcp-server` — зависимостей в репо нет
- Токен передаётся при регистрации

---

## Скиллы Claude Code (`/zoho` и др.)

**Статус: скилл создан, но не подключён через UI**

- Файл скилла написан и сохранён в системную папку скиллов
- Однако `/zoho` как slash-команда не работает — скиллы в Claude Code
  подключаются через UI (Settings → Skills), а не через файловую систему
- **Что сделать:** после стабилизации MCP — установить скиллы через интерфейс

---

## Чеклист для основной машины

- [ ] Проверить / обновить `ZOHO_REFRESH_TOKEN` в `services/ZOHO/config_zoho.env`
- [ ] Положить `voluptas-488008-e88abce2f685.json` в `services/lighthouse/creds/`
- [ ] Зарегистрировать Zoho MCP: `claude mcp add zoho --scope user -- ...`
- [ ] Зарегистрировать Lighthouse MCP: `claude mcp add lighthouse --scope user -- ...`
- [ ] Проверить статусы: попросить Claude `get_status` для обоих MCP
- [ ] Docmost и Qase — проверить что работают (должны, если уже были настроены)

---

## Команды регистрации (актуальные пути для macOS + Claude Code Desktop)

```bash
# Zoho
claude mcp add zoho --scope user -- \
  /Users/$USER/.hermes/hermes-agent/venv/bin/python \
  $(pwd)/services/ZOHO/mcp_server.py

# Lighthouse
claude mcp add lighthouse --scope user -- \
  /Users/$USER/.hermes/hermes-agent/venv/bin/python \
  $(pwd)/services/lighthouse/mcp_server.py
```

Запускать из корня проекта (`pytest_template_SkyPro/`).
