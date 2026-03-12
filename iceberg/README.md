# Iceberg: хранилище данных (датаинженер Iceberg)

Схемы, каталог, партиционирование и обслуживание таблиц Apache Iceberg. Бэкенд: **Hive Metastore** (Thrift), хранилище — **MinIO** (S3-совместимый), путь warehouse `s3a://warehouse`.

См. [Архитектура](../docs/ARCHITECTURE.md) (раздел «Слои данных», «Хранилище»).

## Содержимое каталога

| Путь | Назначение |
|------|------------|
| **[schema_banner_events.md](schema_banner_events.md)** | Схема потока banner_events: raw, ods, dm (поля, партиции, правила очистки). |
| **[schema_ods_er.md](schema_ods_er.md)** | ODS-слой по ER: все 6 сущностей (fct_banners, cd_banner, installs, fct_actions, cd_campaign, cd_user) и связи. |
| **[schema_ml.md](schema_ml.md)** | Схема слоя ML: ml.user_features, ml.click_predictions. |
| **[catalog/](catalog/)** | Конфигурация каталога: где задаются Trino и Spark (Hive Metastore, MinIO, warehouse). |
| **[ddl/](ddl/)** | DDL для создания схем и таблиц (Trino): справочные запросы и ручное создание. |
| **[partitioning.md](partitioning.md)** | Стратегия партиционирования по таблицам (event_date, date, snapshot_date). |
| **[maintenance.md](maintenance.md)** | Обслуживание: expire_snapshots, remove_orphan_files, rewrite_data_files. |

## Слои данных

- **raw** — сырые данные (banner_events и др.), партиция `event_date`.
- **ods** — нормализованный слой после очистки и дедупликации, партиция `event_date`.
- **dm** — витрины BI (campaign_daily), партиция `date`.
- **ml** — витрины признаков и предсказания (user_features, click_predictions), партиция `snapshot_date`.

## Где создаются и заполняются таблицы

Таблицы в MVP создаются **Spark-скриптами** при записи (см. [spark/README.md](../spark/README.md)):

- raw/ods: `kafka_to_raw.py`, `raw_to_ods.py`, `csv_to_raw_iceberg.py`, `raw_to_ods_iceberg.py`
- dm: `ods_to_dm.py`
- ml: `build_ml_user_features.py`

Чтение: **Trino** (каталог `iceberg`, порт 8082), **Superset** подключается к Trino для дашбордов.

## Конфигурация каталога

- **Trino:** `docker/trino/catalog/iceberg.properties` (Hive Metastore URI, S3 endpoint MinIO, region).
- **Spark:** `docker/spark/spark-defaults.conf` (spark_catalog, warehouse s3a://warehouse, S3A/MinIO).

Подробно: [catalog/README.md](catalog/README.md).

## Горячее / холодное хранение

- **Горячее:** последние 30 дней в Iceberg (быстрые запросы).
- **Холодное:** Parquet по месяцам, политики TTL и перенос старых партиций — по необходимости (см. [partitioning.md](partitioning.md), [maintenance.md](maintenance.md)).
