# DE2026_Dataton

Хакатон, кейс Билайна. Задача: построить платформу данных для телеком-компании — от приёма событий до дашбордов и ML-модели.

Поток данных: **источники → Kafka → Spark → Iceberg (MinIO) → Trino → Superset**. Плюс XGBoost для прогноза клика по баннеру. Всё в Docker, одна команда на запуск.

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d
```

После старта нужно создать топики Kafka:

```bash
./kafka/create_topic.sh
# Windows: .\kafka\create_topic.ps1
```

Доступные сервисы (порты из `.env`, тут значения по умолчанию):

- **Airflow** — `http://localhost:8080` (admin / admin)
- **Trino** — `http://localhost:8082` (каталог `iceberg`)
- **Superset** — `http://localhost:8088`
- **MinIO** — `http://localhost:9001` (логин/пароль в `.env`)
- **Spark UI** — `http://localhost:8081`
- **Kafka UI** — `http://localhost:8090`

Подробнее по настройке: [`docker/README.md`](docker/README.md).

## Как устроено

Данные могут приходить двумя путями: CSV-файлы из `sample_data/` (готовые датасеты от организаторов) или симуляция событий через Kafka-продюсер. Дальше:

```
CSV / Kafka events
    ↓ Spark (PySpark)
RAW — сырые данные в Iceberg
    ↓ Spark
ODS — очищенные, типизированные таблицы
    ↓ Spark
DM — витрины для BI (campaign_daily: показы, клики, CPM, CPC)
    ↓ Spark
ML — признаки и предсказания (user_features, прогноз клика)
    ↓
Trino (SQL) ← читает всё из Iceberg
Superset ← дашборды через Trino
```

Оркестрация — Airflow. Три DAG'а:

| DAG | Что делает |
|-----|------------|
| `banner_events_pipeline` | Читает Kafka-топик `banner_events` → raw → ods → dm.campaign_daily |
| `csv_pipeline` | Грузит CSV из sample_data → raw → ods → dm.campaign_daily (полные метрики, CPM/CPC) |
| `ml_daily_pipeline` | Собирает витрину `ml.user_features`, гоняет модель |

Топики Kafka: `banner_events`, `installs`, `actions`, `raw_actions`, `control-iceberg`, `filebeat-logs`. Создаются скриптом из `kafka/`.

## Что внутри

Проект разбит по компонентам, у каждого свой README:

- **airflow/** — DAG'и, конфиги, запуск Spark-задач
- **kafka/** — топики, конфиги Connect/Debezium, продюсер-симулятор
- **spark/** — скрипты ETL (raw→ods, витрины, ML-признаки)
- **iceberg/** — DDL-схемы таблиц (raw, ods, dm, ml), партиционирование
- **ml/** — обучение XGBoost и инференс модели
- **docker/** — конфиги контейнеров (Hive, Trino, Spark, инит Postgres)
- **bi/** — датасеты Superset, подключение к Trino
- **docs/** — архитектура, отчёт по кейсу, SQL эталонной витрины, слайды защиты
- **sample_data/** — исходные CSV для загрузки
- **data_quality/** — скрипты проверки качества при загрузке CSV→raw и raw→ods

## Документация

Основной отчёт по хакатону: [`docs/CASE_REPORT.md`](docs/CASE_REPORT.md).

SQL витрины: [`docs/sql/dm_campaign_daily.sql`](docs/sql/dm_campaign_daily.sql). Загрузка в Trino: [`docs/sql/trino/README.md`](docs/sql/trino/README.md).

Дашборды Superset: [`docs/SUPERSET_MVP.md`](docs/SUPERSET_MVP.md), [`bi/README.md`](bi/README.md).

## Остановка

```bash
docker compose down
# с удалением данных (БД, MinIO, Kafka):
docker compose down -v
```
