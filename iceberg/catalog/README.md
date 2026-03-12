# Каталог Iceberg: конфигурация

Единый каталог Iceberg в проекте — **Hive Metastore** (Thrift). Warehouse — **MinIO** (S3-совместимый), путь `s3a://warehouse` (Spark) / бакет `warehouse` (S3 endpoint).

## Где задаётся конфигурация

| Компонент | Файл | Назначение |
|-----------|------|------------|
| **Trino** | `docker/trino/catalog/iceberg.properties` | Каталог `iceberg`, подключение к Hive Metastore и MinIO |
| **Spark** | `docker/spark/spark-defaults.conf` | Каталог `spark_catalog` (Hive), warehouse `s3a://warehouse`, S3A/MinIO |

## Параметры (актуальные значения)

- **Hive Metastore URI:** `thrift://hive-metastore:9083`
- **Warehouse (Spark):** `s3a://warehouse`
- **MinIO endpoint:** `http://minio:9000` (внутри Docker), path-style access
- **Учётные данные MinIO:** по умолчанию `minioadmin` / `minioadmin` (переменные окружения в docker-compose)
- **Формат файлов:** PARQUET
- **S3 region (Trino):** `us-east-1` (требуется для AWS SDK при работе с MinIO)

## Схемы (базы) в каталоге

После инициализации ETL в каталоге присутствуют схемы:

- **raw** — сырые данные (banner_events и др.)
- **ods** — нормализованный слой
- **dm** — витрины BI (campaign_daily)
- **ml** — витрины признаков и предсказания (user_features, click_predictions)

Создание схем: через Spark (`CREATE DATABASE IF NOT EXISTS raw` и т.д. в скриптах) или через Trino `CREATE SCHEMA IF NOT EXISTS iceberg.raw;`.

## Проверка из Trino

```sql
SHOW SCHEMAS IN iceberg;
SHOW TABLES IN iceberg.raw;
SELECT * FROM iceberg.dm.campaign_daily LIMIT 10;
```

## Проверка из Spark

Таблицы доступны как `spark_catalog.raw.banner_events`, `spark_catalog.ods.banner_events` и т.д. (см. скрипты в `spark/scripts/`).
