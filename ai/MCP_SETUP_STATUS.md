# MCP Setup Status

Этот файл описывает состояние MCP-интеграций на обеих машинах.
Обновляется вручную при изменении конфигурации.

---

## Итоговое состояние (актуально на 2026-06-12)

| Сервер | macOS (MacBook Air M) | Windows 11 (основная) | Scope |
|---|---|---|---|
| **Lighthouse** | ✅ Connected | ✅ Connected | user |
| **Zoho Projects** | ✅ Connected | ✅ Connected | user |
| **Docmost** | ✅ Connected | не проверено | user |
| **Qase** | ✅ Connected | не проверено | user |

Оба наших MCP-сервера зарегистрированы в **user scope** (`~/.claude.json`) — доступны
во всех проектах и в Claude.ai глобально. `.mcp.json` в корне проекта — пустой (нет
дублирования, нет конфликтов).

---

## Lighthouse MCP (`services/lighthouse/mcp_server.py`)

**Python:** `C:\Program Files\Python\Python313\python.exe` (Python 3.13.1) — имеет пакет `mcp`.
**Скрипт:** `C:\Study\pytest_template_SkyPro\services\lighthouse\mcp_server.py`
**Рабочая директория:** сервер сам делает `os.chdir(ROOT_DIR)` через `__file__` — независим от cwd.

### Команда регистрации (Windows, user scope)
```powershell
claude mcp add lighthouse --scope user -e PYTHONUNBUFFERED=1 -e PYTHONIOENCODING=utf-8 -- `
  "C:\Program Files\Python\Python313\python.exe" `
  "C:\Study\pytest_template_SkyPro\services\lighthouse\mcp_server.py"
```

### Команда регистрации (macOS, user scope)
```bash
claude mcp add lighthouse --scope user \
  -e PYTHONUNBUFFERED=1 -e PYTHONIOENCODING=utf-8 -- \
  /Users/$USER/.hermes/hermes-agent/venv/bin/python \
  /Users/aqa/PycharmProjects/pytest_template_SkyPro/services/lighthouse/mcp_server.py
```

**Зависимость:** файл Google credentials (`services/lighthouse/creds/voluptas-488008-e88abce2f685.json`)
gitignored — хранится только на машинах с доступом к Google Sheets.

---

## Zoho Projects MCP (`services/ZOHO/mcp_server.py`)

**Python:** `C:\Program Files\Python\Python313\python.exe` (Python 3.13.1)
**Скрипт:** `C:\Study\pytest_template_SkyPro\services\ZOHO\mcp_server.py`
**Логи:** `Reports/zoho_mcp.log`
**Конфиг:** `services/ZOHO/config_zoho.env` — содержит `ZOHO_ACCESS_TOKEN` + `ZOHO_REFRESH_TOKEN`.

### Команда регистрации (Windows, user scope)
```powershell
claude mcp add zoho --scope user -e PYTHONUNBUFFERED=1 -e PYTHONIOENCODING=utf-8 -- `
  "C:\Program Files\Python\Python313\python.exe" `
  "C:\Study\pytest_template_SkyPro\services\ZOHO\mcp_server.py"
```

### Команда регистрации (macOS, user scope)
```bash
claude mcp add zoho --scope user \
  -e PYTHONUNBUFFERED=1 -e PYTHONIOENCODING=utf-8 -- \
  /Users/$USER/.hermes/hermes-agent/venv/bin/python \
  /Users/aqa/PycharmProjects/pytest_template_SkyPro/services/ZOHO/mcp_server.py
```

**Проблема:** `ZOHO_ACCESS_TOKEN` может протухнуть. При пустом ответе `get_portals()`:
1. Проверь `services/ZOHO/config_zoho.env` — актуален ли `ZOHO_REFRESH_TOKEN`
2. `python services/ZOHO/mcp_server.py` запусти вручную, смотри лог `Reports/zoho_mcp.log`
3. При необходимости обнови токен через Zoho Developer Console

---

## Docmost MCP

Установлен глобально. Исходники: `~/.claude/mcp-servers/docmost-mcp/`.
При переносе — клонировать и собрать отдельно.

---

## Qase MCP

Запускается через `npx @qase/mcp-server`. Токен передаётся при регистрации.

---

## Проверка статуса

```bash
claude mcp list
```

Нормальный вывод для наших серверов:
```
lighthouse: ... - ✓ Connected
zoho: ... - ✓ Connected
```

Если `✗ Failed` — проверить: версия Python, наличие пакета `mcp`, путь к скрипту.

---

## Скиллы / инструкции по MCP

Плагин-система Claude Code **не поддерживает** локальные постоянные скиллы:
- `installed_plugins.json` перезаписывается Claude Code при рестарте
- `--plugin-dir` работает только для текущей сессии
- `claude plugin marketplace add` принимает только URL/GitHub, не локальные пути

**Решение:** инструкции по всем 4 MCP написаны в `~/.claude/CLAUDE.md`.  
Этот файл всегда загружается в контекст любого чата на этом компе.  
Триггеры описаны там — `/zoho`, `/qase`, `/docmost`, `/lighthouse`.

При переезде на новую машину — скопировать `~/.claude/CLAUDE.md`.

---

## Чеклист при переезде на новую машину

- [ ] Установить Python с пакетом `mcp` (`pip install mcp`)
- [ ] Положить `services/lighthouse/creds/voluptas-488008-e88abce2f685.json`
- [ ] Заполнить `services/ZOHO/config_zoho.env` (токены Zoho)
- [ ] Заполнить `services/lighthouse/configs/config_lighthouse.env` (API key, Sheet ID)
- [ ] Зарегистрировать Lighthouse: `claude mcp add lighthouse --scope user ...`
- [ ] Зарегистрировать Zoho: `claude mcp add zoho --scope user ...`
- [ ] Проверить: `claude mcp list` — оба Connected
- [ ] Docmost и Qase — зарегистрировать отдельно
- [ ] Скопировать `~/.claude/CLAUDE.md` — содержит инструкции по всем MCP
