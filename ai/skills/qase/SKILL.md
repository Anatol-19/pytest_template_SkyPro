---
name: qase
description: >
  Work with Qase TMS: manage test cases, test runs, results, defects, suites,
  plans, environments and milestones. Use this skill whenever the user mentions
  Qase, test cases, test runs, test results, defects in TMS, says "создай кейс",
  "запусти прогон", "залогируй результат", "добавь дефект в Qase", "покажи кейсы",
  "какие проекты в Qase". Invoke proactively for any test management topic.
---

# Qase TMS Skill

Доступ к Qase TMS через MCP. Управление тест-кейсами, прогонами и дефектами.

## Ключевые инструменты

### Проекты
- `qase_list_projects` — список всех проектов
- `qase_get_project(code)` — детали проекта

### Тест-кейсы
- `qase_list_cases(project_code)` — список кейсов
- `qase_get_case(project_code, case_id)` — детали кейса
- `qase_create_case(project_code, title, ...)` — создать кейс
- `qase_update_case(...)` — обновить кейс
- `qase_bulk_create_cases(...)` — создать несколько кейсов сразу
- `qase_delete_case(...)` — удалить кейс

### Тест-раны (прогоны)
- `qase_list_runs(project_code)` — список прогонов
- `qase_create_run(project_code, title, cases)` — создать прогон
- `qase_complete_run(project_code, run_id)` — завершить прогон
- `qase_get_run_public_link(...)` — получить публичную ссылку

### Результаты
- `qase_create_result(project_code, run_id, case_id, status)` — залогировать результат
- `qase_create_results_bulk(...)` — несколько результатов сразу
- Статусы: `passed` / `failed` / `blocked` / `skipped` / `invalid`

### Дефекты
- `qase_create_defect(project_code, title, severity)` — создать дефект
- `qase_list_defects(project_code)` — список дефектов
- `qase_resolve_defect(project_code, defect_id)` — закрыть дефект

### Суиты (папки кейсов)
- `qase_list_suites(project_code)` — структура суитов
- `qase_create_suite(project_code, title, parent_id)` — создать суит

## Типичные сценарии

### "Создай тест-кейс"
Нужно минимум: project_code, title. Спроси если не хватает.
Опционально: suite_id, description, preconditions, steps, severity, priority.

### "Запусти прогон"
```
create_run(project_code, title, cases=[id1, id2, ...])
→ возвращаю run_id
```

### "Залогируй результат"
```
create_result(project_code, run_id, case_id, status="passed"/"failed")
```

### "Создай дефект"
```
create_defect(project_code, title, severity="major"/"minor"/"critical"/"blocker")
```

## Форматирование ответов

- Кейсы: показывай ID, title, статус, suite
- Прогоны: показывай ID, title, статус, кол-во кейсов
- Дефекты: показывай ID, title, severity, статус
