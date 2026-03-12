# Обслуживание Iceberg (maintenance)

Рекомендуемые операции для поддержки хранилища: управление снимками и файлами (датаинженер Iceberg).

## 1. Устаревание снимков (expire_snapshots)

Удаляет старые метаданные снимков и позволяет физически удалять файлы, на которые больше нет ссылок.

**Spark (пример):**

```python
# В скрипте Spark с подключением к Iceberg
spark.sql("CALL spark_catalog.system.expire_snapshots(table => 'spark_catalog.raw.banner_events', older_than => TIMESTAMP '2025-01-01 00:00:00')")
```

**Trino:** вызов процедуры `iceberg.system.expire_snapshots` (синтаксис зависит от версии коннектора).

Рекомендация: запускать периодически (например раз в сутки) с порогом `older_than` = «текущее время минус N дней» (например 7–30 дней), чтобы сохранять только нужную историю снимков.

## 2. Удаление «осиротевших» файлов (remove_orphan_files)

Удаляет файлы в warehouse, которые больше не принадлежат ни одному снимку (после expire_snapshots или сбоев записи).

**Spark:**

```python
spark.sql("CALL spark_catalog.system.remove_orphan_files(table => 'spark_catalog.raw.banner_events', older_than => TIMESTAMP '2025-01-01 00:00:00')")
```

Запускать после expire_snapshots; `older_than` — не трогать недавно созданные файлы (например 1–3 дня).

## 3. Компакция (rewrite_data_files)

Объединяет мелкие файлы в более крупные для ускорения чтения и снижения количества объектов в MinIO/S3.

**Spark:**

```python
spark.sql("CALL spark_catalog.system.rewrite_data_files(table => 'spark_catalog.ods.banner_events', where => 'event_date >= DATE \"2025-03-01\"')")
```

Имеет смысл для партиций, в которые часто пишутся небольшие апдейты (streaming, частые batch-вставки).

## 4. Интеграция с Airflow

Рекомендуется вынести вызовы в отдельные задачи DAG (например раз в день):

1. `expire_snapshots` для raw, ods, dm, ml (с порогом 7–30 дней).
2. `remove_orphan_files` после expire_snapshots.
3. Опционально: `rewrite_data_files` для выбранных таблиц/партиций по расписанию.

Скрипты можно оформить как Spark job (отдельный скрипт в `spark/scripts/` или вызов через `spark-submit` с SQL) или через Trino, если коннектор поддерживает процедуры.
