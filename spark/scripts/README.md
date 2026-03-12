# Каталог Spark-скриптов (инженер Spark)

Скрипты в `spark/scripts/` монтируются в контейнер как `/opt/spark/app/scripts`. Запуск: `spark-submit` из контейнера **spark-master** (или через Airflow DAG).

## Поток banner_events (MVP, Kafka → витрина)

| Скрипт | Вход | Выход | Пакеты | Задача Airflow |
|--------|------|-------|--------|----------------|
| **kafka_to_raw.py** | Kafka топик `banner_events` | raw.banner_events (Iceberg) | Iceberg + Kafka | kafka_to_raw |
| **raw_to_ods.py** | raw.banner_events | ods.banner_events (Iceberg) | Iceberg | raw_to_ods |
| **ods_to_dm.py** | ods.banner_events | dm.campaign_daily (Iceberg) | Iceberg | ods_to_dm |

## Загрузка из CSV (качество данных)

| Скрипт | Вход | Выход | Пакеты |
|--------|------|-------|--------|
| **csv_to_raw_iceberg.py** | CSV из `sample_data/` (в контейнере: /sample_data, env CSV_BASE_PATH) | raw.* (Iceberg): fct_banners_show, installs, fct_actions, cd_* | Iceberg |
| **raw_to_ods_iceberg.py** | raw.* (Iceberg) | ods.* (Iceberg), правила аналитика | Iceberg |
| **ods_to_dm_full.py** | ods.fct_banners, ods.installs, ods.fct_actions | dm.campaign_daily (полные метрики: CTR, CPC, CPM, конверсия, revenue) | Iceberg |

## ML

| Скрипт | Вход | Выход | Пакеты |
|--------|------|-------|--------|
| **build_ml_user_features.py** | ods.banner_events (опционально ods.fct_actions, ods.cd_user) | ml.user_features (Iceberg) | Iceberg |

Аргументы: опционально `--snapshot-date YYYY-MM-DD`. См. [ml/README.md](../../ml/README.md).

## Команды запуска (примеры)

Все из корня репозитория при поднятом стеке:

```bash
# Kafka → raw → ods → dm (одна цепочка)
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3,org.apache.spark:spark-sql-kafka_2.12:3.5.0 \
  /opt/spark/app/scripts/kafka_to_raw.py

docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/raw_to_ods.py

docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/ods_to_dm.py
```

Полный список команд — в [spark/README.md](../README.md).

## Зависимости между скриптами

- **kafka_to_raw** → **raw_to_ods** → **ods_to_dm**: строгий порядок; в Airflow задаётся графом задач.
- **csv_to_raw_iceberg** и **raw_to_ods_iceberg**: альтернативный путь наполнения raw/ods из файлов; не зависят от Kafka.
- **build_ml_user_features**: читает ods.banner_events; можно запускать после raw_to_ods (или raw_to_ods_iceberg), отдельно от ods_to_dm.
