# Docker Compose — стек DE2026_Dataton

Локальный запуск платформы данных (кейс Билайн): Kafka, Airflow, Spark, Iceberg (MinIO + Hive Metastore), Trino, Superset.

## Требования

- Docker и Docker Compose (v2+)
- Порты: 5432, 2181, 9092, 9000, 9001, 9083, 8080, 8081, 7077, 8082, 8088, 6379

## Быстрый старт

```bash
# из корня репозитория
cp .env.example .env
# при необходимости отредактируйте .env

docker compose up -d

# Дождаться готовности (особенно postgres, airflow-webserver). Затем:
# Создать админа Superset (логин/пароль по желанию):
docker compose exec superset superset fab create-admin \
  --username admin --firstname Admin --lastname User --email admin@local --password admin
docker compose exec superset superset db upgrade
docker compose exec superset superset init
```

## Сервисы и порты

| Сервис            | Порт(ы)   | Описание |
|-------------------|-----------|----------|
| **PostgreSQL**    | 5432      | БД Airflow, Superset и Hive Metastore (hivemeta) |
| **MinIO**         | 9000, 9001| S3-хранилище (API и консоль) |
| **Zookeeper**     | 2181      | Для Kafka |
| **Kafka**         | 9092      | Брокер |
| **Hive Metastore**| 9083      | Каталог Iceberg |
| **Airflow**       | 8080      | Веб-интерфейс |
| **Spark Master**  | 8081, 7077| UI и master |
| **Trino**         | 8082      | SQL к Iceberg |
| **Superset**      | 8088      | BI-дашборды |

## Первый запуск

1. **MinIO:** консоль http://localhost:9001 — логин/пароль из `.env` (по умолчанию minioadmin/minioadmin). Создайте бакет `warehouse` (или он будет создан при первой записи через Spark/Trino при правильном пути s3a://warehouse/).

2. **Airflow:** http://localhost:8080 — логин `admin`, пароль задаётся при инициализации (по умолчанию в образе может быть `admin`).

3. **Trino:** подключение к Iceberg через каталог `iceberg`. Пример:
   ```sql
   SHOW SCHEMAS IN iceberg;
   CREATE TABLE iceberg.raw.example (id int, ts timestamp) USING iceberg;
   ```

4. **Superset:** после `superset fab create-admin` и `superset init` — http://localhost:8088, логин/пароль те, что задали при create-admin. Подключение к Trino и дашборд MVP: [docs/SUPERSET_MVP.md](../docs/SUPERSET_MVP.md).

## Конфигурация

- **Hive Metastore:** образ `apache/hive:4.0.0` (сборка в `docker/hive/Dockerfile` с драйвером PostgreSQL). Параметры задаются через `SERVICE_OPTS` в `docker-compose.yml`; доступ к MinIO — через `docker/hive/core-site.xml` (монтируется в контейнер).
- **Trino:** `docker/trino/config.properties`, `docker/trino/catalog/iceberg.properties` — каталог Iceberg и S3 (MinIO).
- **Spark:** `docker/spark/spark-defaults.conf` — каталог Hive и S3A (MinIO).

Пароль пользователя Hive в Postgres (БД `hivemeta`) задаётся в `.env` как `METASTORE_DB_PASSWORD` и передаётся в контейнер postgres (init) и hive-metastore (SERVICE_OPTS).

## Остановка

```bash
docker compose down
# с удалением объёмов (данные БД и MinIO будут потеряны):
docker compose down -v
```

## Устранение неполадок: Hive Metastore

- Используется образ **apache/hive:4.0.0** (сборка в `docker/hive/Dockerfile`), метаданные — в PostgreSQL (БД `hivemeta`). Проблемы DumpDirCleanerTask / PartitionExpressionForMetastore в этом образе не воспроизводятся.
- При первой сборке: `docker compose build hive-metastore` (скачивается образ и драйвер PostgreSQL).
- Если схема уже создана и нужно переинициализировать: `docker compose down -v`, затем `docker compose up -d` (данные Postgres и др. будут удалены).

## Устранение неполадок: Kafka

- **kafka failed to start / dependency kafka failed to start** — посмотрите логи: `docker compose logs kafka`. Если брокер падает при старте (например, из‑за недоступности `host.docker.internal` в старых средах), временно перейдите на один listener: в сервисе `kafka` удалите `KAFKA_LISTENERS`, `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP`, `KAFKA_INTER_BROKER_LISTENER_NAME`, блок `extra_hosts` и второй порт `29092:29092`, а в `KAFKA_ADVERTISED_LISTENERS` оставьте только `PLAINTEXT://kafka:9092`. Контейнеры по‑прежнему подключатся к `kafka:9092`; с хоста используйте `localhost:9092`.
