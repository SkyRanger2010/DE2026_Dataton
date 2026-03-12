# Spark (инженер Spark)

ETL: загрузка raw → ODS, дедупликация, построение витрин.

- Очистка (удаление `NULL user_id`).
- Дедупликация по `(banner_id, user_id, event_ts)`.
- Витрины для BI (`dm.campaign_daily`) и для ML (подготовка признаков).

См. [Архитектура](../docs/ARCHITECTURE.md).

## Содержимое каталога (инженер Spark)

| Путь | Назначение |
|------|------------|
| **[config/](config/)** | Конфигурация: spark-defaults.conf, пакеты Iceberg/Kafka, Ivy. |
| **[scripts/](scripts/)** | ETL-скрипты. Каталог и команды: [scripts/README.md](scripts/README.md). |
| **[operations.md](operations.md)** | Эксплуатация: зависимости, типичные сбои, порядок запуска. |

## MVP: ETL-скрипты

Скрипты в `spark/scripts/` монтируются в контейнер Spark как `/opt/spark/app`. Запуск через `spark-submit` из контейнера `spark-master` (или с хоста: `docker compose exec spark-master ...`).

### 1. Kafka → raw.banner_events

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3,org.apache.spark:spark-sql-kafka_2.12:3.5.0 \
  /opt/spark/app/scripts/kafka_to_raw.py
```

### 2. raw → ods.banner_events

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/raw_to_ods.py
```

### 3. ods → dm.campaign_daily

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/ods_to_dm.py
```

### 4. CSV (sample_data) → raw (Iceberg), качество данных

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/csv_to_raw_iceberg.py
```

### 5. raw (Iceberg) → ods (Iceberg), правила аналитика

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/raw_to_ods_iceberg.py
```

### 6. ods → dm.campaign_daily (полные метрики, CSV-поток)

После raw_to_ods_iceberg можно собрать витрину с installs, conversions, revenue, CPC, CPM (скрипт `ods_to_dm_full.py`). Запускается из DAG `csv_pipeline`.

Каталог и warehouse заданы в `docker/spark/spark-defaults.conf` (Hive Metastore, S3A/MinIO).

### 7. Витрина признаков для ML (ml.user_features)

Построение витрины для модели прогноза клика (XGBoost). См. [ml/README.md](../ml/README.md), [iceberg/schema_ml.md](../iceberg/schema_ml.md).

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/build_ml_user_features.py
```
