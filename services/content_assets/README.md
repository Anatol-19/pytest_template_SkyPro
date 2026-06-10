# Content assets API checks

Проверки валидируют CSV-выгрузку видео против content API:

- логинятся мембером через `/proxy-user/api/wp/auth/login`;
- запрашивают пост по `slug` через `/proxy/api/content/v1/post/{slug}`;
- сверяют ожидаемые asset paths из CSV с signed CDN URLs из API;
- проверяют наличие `ttl` и `token`;
- опционально проверяют signed URL HTTP-запросом.

## ENV

Создайте локальный `.env` в корне проекта:

```env
VRP_MEMBER_EMAIL=qa_active@mailto.plus
VRP_MEMBER_PASSWORD=...
```

Токены не сохраняются в файлы и живут только в `requests.Session`.

## Запуск

```bash
pytest test/test_content_assets.py \
  --environment=VRP_PROD \
  --assets-csv="/path/to/Result_2.csv"
```

Для легкой проверки первых N видео:

```bash
pytest test/test_content_assets.py \
  --environment=VRP_PROD \
  --assets-csv="/path/to/Result_2.csv" \
  --asset-limit=3
```

Для проверки доступности CDN URLs:

```bash
pytest test/test_content_assets.py \
  --environment=VRP_PROD \
  --assets-csv="/path/to/Result_2.csv" \
  --check-http
```

## Отчеты

По умолчанию рядом с исходным CSV создаются:

- `{name}_asset_report.csv` — детальный отчет, одна строка на asset.
- `{name}_verified.csv` — summary по видео.

Пути можно переопределить:

```bash
--asset-report=/path/to/detail.csv
--asset-summary=/path/to/summary.csv
```
