# DE2026_Dataton

Платформа данных для телеком-компании (кейс **Билайн**): единое хранилище, ETL-пайплайны, BI и ML. Поток данных: **источники → Kafka → Spark → Iceberg (MinIO) → Trino / Superset**.

---

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d
```

После запуска создать топики Kafka (из корня репо):

```bash
./kafka/create_topic.sh
# или на Windows: .\kafka\create_topic.ps1
```

**Сервисы и порты** (по умолчанию, порты задаются в `.env`):

| Сервис | URL | Назначение |
|--------|-----|------------|
| **Airflow** | http://localhost:8080 | Оркестрация пайплайнов (логин `admin` / пароль `admin`) |
| **Trino** | http://localhost:8082 | SQL к Iceberg (каталог `iceberg`) |
| **Superset** | http://localhost:8088 | BI-дашборды |
| **MinIO Console** | http://localhost:9001 | S3-хранилище (логин/пароль из `.env`) |
| **Spark UI** | http://localhost:8081 | Мониторинг Spark-задач |
| **Kafka UI** | http://localhost:8090 | Топики и сообщения Kafka |

Подробнее по запуску и настройке: [docker/README.md](docker/README.md).

---

## Архитектура

- **Источники (MVP):** CSV ([sample_data/](sample_data/)) и/или симуляция событий в Kafka.
- **Поток:** Kafka → Spark (ETL) → Iceberg в MinIO; каталог таблиц — Hive Metastore.
- **Слои данных:** raw → ods → dm (витрины BI), ml (признаки и предсказания).
- **Потребление:** Trino (SQL), Superset (дашборды), ML-модель (прогноз клика, рекомендация ставки).

Оркестрация: **Airflow** (DAG-и с зависимостями и retry, запуск Spark через Docker).

Подробно: [docs/CASE_REPORT.md](docs/CASE_REPORT.md), раздел «Реализованное решение».

---

## Пайплайны (Airflow DAG-и)

| DAG | Назначение |
|-----|------------|
| **banner_events_pipeline** | Kafka (топик `banner_events`) → raw → ods → dm.campaign_daily |
| **csv_pipeline** | CSV (sample_data) → raw → ODS → dm.campaign_daily (полные метрики, CPM/CPC) |
| **ml_daily_pipeline** | Сбор витрины признаков ml.user_features для модели прогноза клика |

Топики создаются скриптом [kafka/create_topic.sh](kafka/create_topic.sh) (или [kafka/create_topic.ps1](kafka/create_topic.ps1)): `banner_events`, `installs`, `actions`, `raw_actions`, `control-iceberg`, `filebeat-logs`.

---

## Структура репозитория

| Каталог | Назначение |
|---------|------------|
| **airflow/** | DAG-и, конфигурация, запуск Spark-задач; [airflow/dags/README.md](airflow/dags/README.md), [airflow/operations.md](airflow/operations.md) |
| **kafka/** | Топики, конфиги Connect/Debezium, продюсер симуляции; [kafka/README.md](kafka/README.md) |
| **spark/** | ETL-скрипты (raw→ods, витрины, ML-признаки); [spark/README.md](spark/README.md), [spark/scripts/README.md](spark/scripts/README.md) |
| **iceberg/** | Схемы таблиц (raw, ods, dm, ml), DDL, партиционирование; [iceberg/README.md](iceberg/README.md) |
| **ml/** | Обучение (XGBoost) и инференс модели прогноза клика; [ml/README.md](ml/README.md) |
| **docker/** | Конфиги контейнеров (Hive, Trino, Spark, init Postgres); [docker/README.md](docker/README.md) |
| **docs/** | Архитектура, отчёт по кейсу, описание слайдов защиты; эталонная логика витрины — [docs/sql/dm_campaign_daily.sql](docs/sql/dm_campaign_daily.sql) |
| **docs/sql/trino/** | SQL для загрузки в Trino (демо dm, ml); [docs/sql/trino/README.md](docs/sql/trino/README.md) |
| **bi/** | BI: датасеты, дашборды Superset, подключение к Trino; [bi/README.md](bi/README.md), [docs/SUPERSET_MVP.md](docs/SUPERSET_MVP.md) |
| **sample_data/** | Исходные CSV для загрузки в raw; [sample_data/DESCRIPTION.md](sample_data/DESCRIPTION.md) |
| **data_quality/** | Скрипты загрузки CSV→raw и raw→ods (качество данных); [data_quality/README.md](data_quality/README.md) |

---

## Документация

- **Отчёт по кейсу и критерии выполнения:** [docs/CASE_REPORT.md](docs/CASE_REPORT.md)
- **Слайды защиты:** [PRESENTATION_SLIDES.md](PRESENTATION_SLIDES.md)
- **Superset (подключение, дашборд MVP):** [docs/SUPERSET_MVP.md](docs/SUPERSET_MVP.md)

---

## Остановка

```bash
docker compose down
# с удалением данных (БД, MinIO, Kafka и т.д.):
docker compose down -v
```
