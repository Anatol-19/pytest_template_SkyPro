---
name: zoho
description: >
  Work with Zoho Projects: view tasks, bugs, milestones, users, sprint summaries,
  and create bug reports — all via natural language through the Zoho MCP server.
  Use this skill whenever the user asks about tasks or bugs in Zoho, wants a sprint
  summary, says "покажи задачи", "баги за неделю", "создай баг", "что в Zoho",
  mentions a milestone or tasklist by name, or asks who is responsible for something.
  Invoke proactively when any Zoho Projects topic comes up, even without an explicit
  "/zoho" command.
---

# Zoho Projects Skill

You have access to a Zoho Projects MCP server for the **vrbgroup** portal.
The project contains tasks, bugs, milestones, and a QA/Dev/PM team.

## Available MCP tools

| Tool | What it does | Key params |
|------|-------------|------------|
| `zoho_get_status` | Check API connection | — |
| `zoho_get_tasks` | List tasks with filters | `created_after`, `created_before`, `closed_after`, `closed_before`, `owner_name`, `milestone_name`, `tasklist_name`, `limit` |
| `zoho_get_bugs` | List bugs with filters | `created_after`, `created_before`, `closed_after`, `closed_before`, `owner_name`, `limit` |
| `zoho_get_milestones` | List all milestones | — |
| `zoho_get_tasklists` | List all tasklists | — |
| `zoho_get_users` | List team members | `search` (optional) |
| `zoho_get_tags` | List project tags | — |
| `zoho_create_bug` | Create a new bug | `title`, `description`, `assignee_name` (optional), `priority` (high/medium/low) |
| `zoho_get_tasks_by_title` | Search tasks by tasklist/milestone name | `title` |
| `zoho_get_bug_statuses` | List possible bug statuses | — |

## How to handle requests

### "Show me tasks / bugs"
Call `zoho_get_tasks` or `zoho_get_bugs`. If the user mentions a time period
(e.g. "this week", "last sprint"), convert it to `created_after` / `created_before`
dates (YYYY-MM-DD). If they mention a person, use `owner_name`.

Present results grouped by **status** if there are many, or as a flat list if few.
Do not dump raw data — format it clearly.

### "Sprint summary" or "what happened this week"
Call both `zoho_get_tasks` and `zoho_get_bugs` with the relevant date range.
Summarize: how many tasks open/closed, how many bugs open/closed, who did what.

### "Show milestones / tasklists"
Call `zoho_get_milestones` or `zoho_get_tasklists`. Present as a simple list.

### "Who is responsible for X"
Search tasks/bugs by milestone or tasklist name, then look at owner fields.
Or call `zoho_get_users` to find a person.

### "Create a bug"
You need: title, description. Optionally: assignee_name, priority.
If the user gave enough info, call `zoho_create_bug` directly.
If details are missing, ask — but keep it to one question, not an interview.

### Connection check
If something seems broken or the user asks "does Zoho work?", call `zoho_get_status` first.

## Date handling

Convert natural language to dates:
- "this week" → Monday of current week to today
- "last week" → previous Mon–Sun
- "yesterday" → yesterday's date
- "this month" → first of month to today
- Always use YYYY-MM-DD format

## Output format

Keep results readable:
- Use bullet lists or short tables
- Show: ID, title, status, owner, deadline (if available)
- Group by status when there are 5+ items of the same type
- For sprint summaries use sections: Tasks / Bugs / Summary

## Team quick reference

QA: Анатолий Киселев, Сергей Лысенков, Степан Жиравецкий, Захар Лада,
    Максим Ачаповский, Никита Молостов, Данил Казаков
PM: Денис Турчак, Аким Антропов, Антон Казаков
Dev Front: Данил Бабенков, Федор Гаранин, Владислав Незванов
Dev Back: Мария Алексеева, Владимир Лисевич
DevOps: Алексей Демидов

Use Russian names when addressing the user about team members.

