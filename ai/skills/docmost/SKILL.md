---
name: docmost
description: >
  Read and write pages in the Docmost documentation workspace.
  Use this skill when the user wants to: find documentation, read a page,
  search in docs, says "найди в доке", "что написано про X", "покажи страницу",
  "список страниц". For WRITING — only act when the user gives explicit permission
  in this message: "запиши", "создай страницу", "обнови страницу", "напиши в доку".
  Never write to Docmost proactively or based on vague intent.
---

# Docmost MCP Skill

Доступ к рабочей документации через Docmost MCP.

## ⚠️ Главное правило

**Читать** — можно всегда.
**Писать** (create_page, update_page, delete_page, move_page) — **только если пользователь
явно написал в этом же сообщении** что нужно записать/создать/обновить страницу.
Никогда не создавай и не изменяй страницы по своей инициативе.

## Инструменты

### Чтение (использовать свободно)
- `docmost_get_workspace` — общая информация о воркспейсе
- `docmost_list_spaces` — список спейсов (разделов)
- `docmost_list_pages(space_id)` — страницы в спейсе
- `docmost_get_page(page_id)` — содержимое страницы
- `docmost_search(query)` — полнотекстовый поиск

### Запись (только с явного разрешения)
- `docmost_create_page(space_id, title, content)` — создать страницу
- `docmost_update_page(page_id, title, content)` — обновить страницу
- `docmost_move_page(page_id, parent_id)` — переместить
- `docmost_delete_page(page_id)` — удалить
- `docmost_list_groups` — список групп доступа

## Типичные сценарии

### "Найди документацию по X"
```
docmost_search(query="X")
→ показываю найденные страницы с заголовками и фрагментами
```

### "Покажи структуру доки"
```
docmost_list_spaces()
→ для каждого спейса docmost_list_pages(space_id)
→ показываю дерево
```

### "Покажи страницу про Y"
```
docmost_search("Y") → берём page_id → docmost_get_page(page_id)
→ показываю содержимое
```

### "Запиши это в доку" (явное разрешение)
Уточни space и место (родительская страница) если не указаны.
Затем `create_page` или `update_page`.

## Форматирование ответов

- Для списков страниц: показывай title и краткий путь (space → parent → page)
- Для содержимого: показывай как есть, без лишних обёрток
- При поиске: показывай топ-5 результатов с фрагментом текста
