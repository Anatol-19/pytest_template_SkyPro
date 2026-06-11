# Postman cloud — синхронизация

> Collection ID: `2fce3481-e7d3-4cb7-b282-34edbeef8a0d`
> API key: в памяти агента (`reference_postman.md`) — не хардкодить в коллекцию.
> Скрипт: `/Users/aqa/Documents/postman-work/sync_to_cloud.sh`

---

## Синхронизировать коллекцию в cloud

```bash
bash /Users/aqa/Documents/postman-work/sync_to_cloud.sh PMAK-...
```

Или через переменную окружения:
```bash
export POSTMAN_API_KEY=PMAK-...
bash /Users/aqa/Documents/postman-work/sync_to_cloud.sh
```

Скрипт делает `PUT /collections/{id}` — обновляет существующую коллекцию.

---

## Если коллекция удалена из cloud (нужно создать заново)

```bash
curl -s -X POST "https://api.getpostman.com/collections" \
  -H "x-api-key: $POSTMAN_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @<(python3 -c "
import json
with open('/Users/aqa/Documents/postman-work/Payment_final.json') as f:
    data = json.load(f)
print(json.dumps({'collection': data}))
") | python3 -m json.tool
```

После создания: обновить `COLLECTION_ID` в `sync_to_cloud.sh` и в этом файле.

---

## Структурные требования коллекции

Постман cloud ожидает при `PUT`:
```json
{ "collection": { "info": {...}, "item": [...], "event": [...] } }
```

Локально `Payment_final.json` хранится **без обёртки** (корень = `info/item/event`) —
так работает Newman. Скрипт добавляет обёртку `{"collection": ...}` только при загрузке.

### Обязательные условия перед синком

- `info._postman_id` заполнен
- Все `id` у запросов и папок уникальны (нет дублей, нет пустых)
- Нет лишней обёртки `{"collection": ...}` в локальном файле

Проверить:
```bash
python3 -c "
import json, collections
with open('/Users/aqa/Documents/postman-work/Payment_final.json') as f:
    d = json.load(f)
assert 'info' in d and 'item' in d, 'Нет обёртки — OK'

def ids(items):
    for i in items:
        if 'id' in i: yield i['id']
        if 'item' in i: yield from ids(i['item'])
all_ids = list(ids(d['item']))
dupes = [k for k,v in collections.Counter(all_ids).items() if v > 1]
print('Дубликатов ID:', len(dupes))
print('Всего запросов/папок:', len(all_ids))
print('Root keys:', list(d.keys()))
"
```

---

## После изменений в Python — когда синкать

Синкать в cloud **после**:
1. Newman-прогон прошёл без ошибок
2. Пользователь явно попросил синкнуть

Не синкать автоматически — каждый синк перезаписывает коллекцию в облаке.
