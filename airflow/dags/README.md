# DAG-и Airflow

Пайплайны подгружаются из `airflow/dags/` (в Docker — `/opt/airflow/dags`). Зависимости по архитектуре: справочники/сырые данные → ODS → витрины. У всех DAG включены retries; алерты в Telegram настраиваются через `on_failure_callback` и переменные окружения (см. operations.md).

## Список DAG-ов

| DAG ID | Расписание | Описание | Задачи |
|--------|------------|----------|--------|
| **banner_events_pipeline** | @daily | События из Kafka → витрина по кампаниям | kafka_to_raw → raw_to_ods → ods_to_dm |
| **csv_pipeline** | @daily | Загрузка из CSV (sample_data) → ODS → полная витрина | csv_to_raw_iceberg → raw_to_ods_iceberg → ods_to_dm_full |
| **ml_daily_pipeline** | @daily | Витрина признаков для ML (прогноз клика) | build_ml_user_features |

## Как устроен запуск Spark

Каждая задача вызывает `run_spark_script()` из `spark_runner`: ищется контейнер `spark-master`, в нём выполняется `spark-submit` с нужными `--packages` (Iceberg/Kafka). Нужны доступ к Docker socket и пакет `docker` в образе Airflow.

### Добавить новую задачу

1. В DAG — функция с `@task`, внутри вызов `run_spark_script("скрипт.py", PACKAGES_ICEBERG)` или `PACKAGES_KAFKA`.
2. Зависимости: `task_a() >> task_b()`.
3. Скрипт должен быть в `spark/scripts/` (в контейнере — `/opt/spark/app/scripts/`).
