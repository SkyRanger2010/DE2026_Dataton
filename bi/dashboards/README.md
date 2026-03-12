# Экспорт дашбордов Superset

Сюда сохраняют экспорты дашбордов для переноса в репозиторий и на другие инстансы Superset.

## Экспорт

1. В Superset откройте дашборд (например «Эффективность кампаний»).
2. **Dashboard → Export → Export dashboard (YAML)** (или Export as JSON, в зависимости от версии).
3. Сохраните файл в `bi/dashboards/`, например `campaign_effectiveness.yaml`.

## Импорт

1. **Data → Import dashboards** (или через CLI: `superset import-dashboards -p path/to/file.yaml`).
2. Укажите файл из `bi/dashboards/`.
3. Проверьте, что подключение к Trino (Database) совпадает с именем в экспорте; при необходимости обновите connection после импорта.

После импорта дашборд появится в списке; чарты будут ссылаться на датасет `dm.campaign_daily` при наличии такого датасета и подключения к Iceberg.
