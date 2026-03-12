# DDL Iceberg

Определения таблиц хранилища для справки и ручного создания.

## Файлы

| Файл | Описание |
|------|----------|
| **tables_trino.sql** | CREATE SCHEMA / CREATE TABLE для Trino (каталог `iceberg`). Подходит для создания пустых таблиц или сверки структуры. |

## Как таблицы создаются в MVP

В основном пайплайне таблицы создаются **Spark-скриптами** при первой записи:

- `raw.banner_events`, `ods.banner_events` — `kafka_to_raw.py`, `raw_to_ods.py`, `csv_to_raw_iceberg.py`, `raw_to_ods_iceberg.py`
- `dm.campaign_daily` — `ods_to_dm.py`
- `ml.user_features` — `build_ml_user_features.py`

Использование Trino DDL нужно, если вы хотите заранее создать пустые таблицы (например для Kafka Iceberg Sink) или воссоздать схему вручную. Подключение к Trino: порт 8082 (хост `trino` из Docker, `localhost:8082` с хоста).

## Схемы таблиц (полное описание)

- [schema_banner_events.md](../schema_banner_events.md) — raw.banner_events, ods.banner_events, dm.campaign_daily
- [schema_ml.md](../schema_ml.md) — ml.user_features, ml.click_predictions
