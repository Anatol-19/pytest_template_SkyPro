# Установка пользовательских скиллов Claude Code

Скиллы работают **только локально** в Cowork/desktop app. При каждом рестарте
Anthropic перезаписывает активный плагин — нужно добавить скиллы снова.

---

## Что здесь

```
ai/skills/
├── zoho/SKILL.md       — Zoho Projects (задачи, баги, спринты)
├── lighthouse/SKILL.md — Lighthouse (аудит производительности)
├── qase/SKILL.md       — Qase TMS (тест-кейсы, запуски, дефекты)
├── docmost/SKILL.md    — Docmost (документация, только чтение без разрешения)
└── INSTALL.md          — этот файл
```

---

## Способ установки (через skill-creator)

Это самый надёжный способ — skill-creator сам разберётся с путями.

1. Открой новый чат в Claude Code (desktop app / Cowork)
2. Напиши: `/skill-creator`
3. Когда скилл загрузится, скажи:

   > "Установи 4 скилла из папки `ai/skills/` проекта pytest_template_SkyPro.
   > Это готовые SKILL.md файлы, не нужно их переписывать — просто добавь в активный плагин."

Skill-creator найдёт активный плагин сессии и скопирует туда файлы.

---

## Ручная установка (если skill-creator недоступен)

### Шаг 1. Найти активный плагин сессии

```bash
ls ~/Library/Application\ Support/Claude/local-agent-mode-sessions/skills-plugin/
```

Там будут 1-2 папки с UUID. Активный плагин — тот у которого `lastUpdated` сегодня:

```bash
for d in ~/Library/Application\ Support/Claude/local-agent-mode-sessions/skills-plugin/*/; do
  echo "$d"
  ls -la "$d"
done
```

### Шаг 2. Найти session UUID внутри плагина

```bash
PLUGIN_DIR="~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/<PLUGIN_UUID>"
ls "$PLUGIN_DIR/"
# Там будет одна папка — это session UUID
```

### Шаг 3. Скопировать SKILL.md файлы

```bash
ACTIVE="$PLUGIN_DIR/<SESSION_UUID>/skills"
PROJECT="/путь/до/pytest_template_SkyPro/ai/skills"

for skill in zoho lighthouse qase docmost; do
  mkdir -p "$ACTIVE/$skill"
  cp "$PROJECT/$skill/SKILL.md" "$ACTIVE/$skill/SKILL.md"
done
```

### Шаг 4. Добавить в manifest.json

Открой `$PLUGIN_DIR/<SESSION_UUID>/manifest.json` и добавь в массив `skills`:

```json
{
  "skillId": "zoho",
  "name": "zoho",
  "description": "Work with Zoho Projects: view tasks, bugs, milestones, users, sprint summaries, and create bug reports via natural language through the Zoho MCP server. Use this skill whenever the user asks about tasks or bugs in Zoho, wants a sprint summary, says \"покажи задачи\", \"баги за неделю\", \"создай баг\", \"что в Zoho\", mentions a milestone or tasklist by name, or asks who is responsible for something. Trigger on /zoho, \"задачи\", \"спринт\", \"состав спринта\", \"следующий релиз\".",
  "creatorType": "user",
  "updatedAt": "2026-06-12T00:00:00.000000Z",
  "enabled": true
},
{
  "skillId": "lighthouse",
  "name": "lighthouse",
  "description": "Run Lighthouse performance tests and CrUX data collection for VRP/VRS environments. Use this skill whenever the user wants to run performance tests, check page speed, collect CrUX data, check test job status, see available environments or routes, says \"запусти лайтхаус\", \"проверь скорость\", \"перф тест\", \"производительность страницы\", \"lighthouse\". Trigger on /lighthouse.",
  "creatorType": "user",
  "updatedAt": "2026-06-12T00:00:00.000000Z",
  "enabled": true
},
{
  "skillId": "qase",
  "name": "qase",
  "description": "Work with Qase TMS: manage test cases, test runs, results, defects, suites, plans. Use this skill whenever the user mentions Qase, test cases, test runs, says \"создай кейс\", \"запусти прогон\", \"залогируй результат\", \"добавь дефект в Qase\", \"покажи кейсы\". Trigger on /qase, \"тест-кейс\", \"тест план\", \"тест сьют\".",
  "creatorType": "user",
  "updatedAt": "2026-06-12T00:00:00.000000Z",
  "enabled": true
},
{
  "skillId": "docmost",
  "name": "docmost",
  "description": "Read and write pages in the Docmost documentation workspace. Use when the user wants to find documentation, read a page, search in docs, says \"найди в доке\", \"что написано про\", \"покажи страницу\", \"docmost\". WRITE only with explicit permission. Trigger on /docmost, \"документация\", \"вики\".",
  "creatorType": "user",
  "updatedAt": "2026-06-12T00:00:00.000000Z",
  "enabled": true
}
```

### Шаг 5. Проверить

Без перезапуска — скиллы появятся сразу. Попробуй `/zoho`.

---

## Примечания

- Скиллы НЕ работают в Claude.ai web — только в desktop app
- После рестарта Claude нужно повторить установку (или попросить `/skill-creator`)
- MCP-серверы (zoho, lighthouse, qase, docmost) должны быть зарегистрированы отдельно — см. `ai/MCP_SETUP_STATUS.md`
