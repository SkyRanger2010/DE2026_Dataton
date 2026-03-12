# Конфигурация Spark (инженер Spark)

## Где задаётся конфиг

- **Файл:** `docker/spark/spark-defaults.conf` — монтируется в контейнеры spark-master и spark-worker. Параметры применяются ко всем job'ам.

## Текущие параметры (spark-defaults.conf)

| Параметр | Значение | Назначение |
|----------|----------|------------|
| spark.sql.extensions | org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions | Поддержка Iceberg в Spark SQL |
| spark.sql.catalog.spark_catalog | org.apache.iceberg.spark.SparkSessionCatalog | Каталог по умолчанию |
| spark.sql.catalog.spark_catalog.type | hive | Тип каталога — Hive |
| spark.sql.catalog.spark_catalog.uri | thrift://hive-metastore:9083 | Hive Metastore (метаданные таблиц) |
| spark.sql.catalog.spark_catalog.warehouse | s3a://warehouse | Путь warehouse (MinIO) |
| spark.hadoop.fs.s3a.* | endpoint, access.key, secret.key, path.style.access, impl | Подключение к MinIO как S3A |

Итог: все таблицы Iceberg (raw, ods, dm, ml) доступны как `spark_catalog.raw.banner_events`, `spark_catalog.ods.banner_events` и т.д.; данные физически в MinIO в бакете warehouse.

## Пакеты (--packages)

Зависимости не в образе, а подтягиваются при spark-submit:

| Набор | Packages | Использование |
|-------|----------|---------------|
| **Iceberg** | org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 | Все скрипты записи/чтения Iceberg |
| **Kafka** | org.apache.spark:spark-sql-kafka_2.12:3.5.0 | Скрипты чтения из Kafka (kafka_to_raw.py) |

Версия Scala — 2.12, версия Spark в образе — согласована с 3.5. При смене образа Spark проверьте совместимость iceberg-spark-runtime и spark-sql-kafka.

## Переменные окружения

В контейнере Spark при необходимости можно задать:

- Путь к приложению: скрипты монтируются как `./spark:/opt/spark/app` (в т.ч. `scripts/` → `/opt/spark/app/scripts`).
- CSV/sample_data: `./sample_data:/sample_data` (в контейнере задаётся CSV_BASE_PATH=/sample_data) — для csv_to_raw_iceberg.py.

Kafka bootstrap задаётся в скриптах (например kafka:9092) или через переменные, если скрипт их читает.

## Ivy cache

При первом запуске `--packages` зависимости скачиваются в `/home/spark/.ivy2`. В docker-compose задан том `spark_ivy_cache` для этого пути, чтобы не качать пакеты при каждом пересоздании контейнера. В DAG Airflow перед spark-submit выполняется `mkdir -p` для каталогов cache/jars на случай отсутствия прав.
