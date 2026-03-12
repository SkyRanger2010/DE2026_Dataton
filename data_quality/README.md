

## Схема

- **raw** — слой Iceberg (таблицы `raw.fct_banners_show`, `raw.installs`, `raw.fct_actions`, `raw.cd_banner`, `raw.cd_campaign`, `raw.cd_user`). Заполняется из CSV (sample_data).
- **ods** — слой Iceberg после очистки и дедупликации (правила аналитика: NULL user_id, дедупликация, расчёт CPM/CPC). Полная модель ODS по ER: **6 сущностей** (fct_banners, cd_banner, installs, fct_actions, cd_campaign, cd_user) и связи — [iceberg/schema_ods_er.md](../iceberg/schema_ods_er.md); иллюстрация — [Аналитик качества данных/ER сущности.png](../Аналитик%20качества%20данных/ER%20сущности.png).

Запросы к raw/ods — через **Trino** (каталог `iceberg`, схемы `raw`, `ods`).

## Шаги

### 1. CSV → raw (Iceberg)

Spark-скрипт читает CSV из каталога `sample_data/` (в контейнере смонтирован как `/opt/spark/app/sample_data`) и пишет в Iceberg `raw.*`.

**Запуск из контейнера spark-master:**

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/csv_to_raw_iceberg.py
```

Путь к CSV можно задать переменной окружения: `CSV_BASE_PATH=/opt/spark/app/sample_data` (по умолчанию уже такой).

### 2. raw (Iceberg) → ods (Iceberg)

Spark-скрипт читает из `raw.*`, применяет правила качества (очистка, дедупликация, CPM/CPC), пишет в `ods.*`.

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/raw_to_ods_iceberg.py
```

## Скрипты

| Скрипт | Назначение |
|--------|------------|
| `spark/scripts/csv_to_raw_iceberg.py` | CSV (sample_data) → raw (Iceberg) |
| `spark/scripts/raw_to_ods_iceberg.py` | raw (Iceberg) → ods (Iceberg), правила качества аналитика |

## Проверка в Trino

```sql
USE iceberg;
SHOW TABLES IN raw;
SHOW TABLES IN ods;
SELECT * FROM raw.fct_banners_show LIMIT 10;
SELECT * FROM ods.fct_banners LIMIT 10;
```

