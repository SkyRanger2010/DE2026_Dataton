# Spark: эксплуатация (инженер Spark)

## Зависимости перед запуском job'ов

1. **spark-master** и **spark-worker** — контейнеры в состоянии running. Без воркера задачи не выполняются.
2. **Hive Metastore** — доступен по `thrift://hive-metastore:9083` (каталог Iceberg).
3. **MinIO** — доступен, бакет `warehouse` создан (minio-init). Spark пишет через S3A в `s3a://warehouse`.
4. Для **kafka_to_raw.py**: **Kafka** доступна, топик `banner_events` создан.
5. Для **csv_to_raw_iceberg.py**: каталог **sample_data** смонтирован в контейнер как `/sample_data` (переменная CSV_BASE_PATH).

## Порядок запуска при «холодном» старте

1. Поднять стек: `docker compose up -d` (включая minio-init, hive-metastore, spark-master, spark-worker, kafka при необходимости).
2. Создать топик Kafka (если используете kafka_to_raw): `./kafka/create_topic.sh` или вручную.
3. Запустить ETL: вручную командами из [scripts/README.md](scripts/README.md) или через Airflow DAG `banner_events_pipeline`.

## Типичные сбои

| Симптом | Возможная причина | Действие |
|--------|-------------------|----------|
| Job висит в ACCEPTED / pending | Нет свободных исполнителей (worker не запущен или перегружен) | Проверить spark-worker, логи master |
| ClassNotFoundException / NoSuchMethod | Несовпадение версий Spark и пакетов (Iceberg, Kafka) | Проверить версии в --packages (2.12, 3.5); при смене образа Spark обновить пакеты |
| Connection refused hive-metastore:9083 | Hive Metastore не запущен или не в сети | `docker compose ps`, сеть dataton |
| S3A Access Denied / 403 | Неверные ключи MinIO или бакет не создан | Проверить spark-defaults (s3a.access.key, secret.key), minio-init |
| Ivy: permission denied в /home/spark/.ivy2 | Нет прав на каталог в контейнере | Убедиться в томе spark_ivy_cache и в DAG Airflow — `mkdir -p` перед spark-submit |
| kafka_to_raw: timeout / no data | Топик пуст или брокер недоступен | Запустить продюсер (kafka/producer_simulate.py) или проверить bootstrap в скрипте |

## Логи и мониторинг

- **Spark UI:** http://localhost:8081 (порт spark-master) — активные и завершённые джобы, стадии, логи исполнителей.
- **Вывод spark-submit:** при запуске через `docker compose exec` вывод в терминале; при запуске из Airflow — в логе задачи Airflow.

## Добавление нового скрипта

1. Создайте файл в `spark/scripts/`, например `my_etl.py`.
2. Используйте `SparkSession.builder.getOrCreate()` и каталог `spark_catalog` (таблицы Iceberg).
3. Запуск вручную: как в [scripts/README.md](scripts/README.md), с нужным `--packages`.
4. Интеграция в Airflow: в DAG добавьте задачу с `run_spark_script("my_etl.py", PACKAGES_ICEBERG)` и нужными зависимостями по графу.

Схемы таблиц: [iceberg/schema_banner_events.md](../iceberg/schema_banner_events.md), [iceberg/schema_ml.md](../iceberg/schema_ml.md).
