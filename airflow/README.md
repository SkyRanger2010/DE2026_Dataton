# Airflow (инженер Airflow)

Оркестрация пайплайнов данных: DAG-и, запуск Spark-задач через Docker API, retry и (по архитектуре) алерты в Telegram.

См. [Архитектура](../docs/ARCHITECTURE.md).

## Содержимое каталога

| Путь | Назначение |
|------|------------|
| **[dags/](dags/)** | DAG-и (графы задач). MVP: `banner_events_pipeline` (Kafka → raw → ods → dm). |
| **[dags/README.md](dags/README.md)** | Описание DAG-ов, как добавить задачу Spark, шаблон вызова. |
| **[config/](config/)** | Конфигурация: Connections, Variables, retry, алерты (инженер Airflow). |
| **[operations.md](operations.md)** | Эксплуатация: зависимости, типичные сбои, ручной запуск, логи. |

## Быстрый старт

- **Web UI:** http://localhost:8080 (после `docker compose up` и инициализации админа).
- **Основной DAG:** `banner_events_pipeline` — включите (Unpause) и запустите вручную или дождитесь расписания (@daily).
- Задачи выполняют spark-submit в контейнере **spark-master**; должны быть запущены spark-master, spark-worker, Kafka, MinIO, Hive Metastore.

## Управление загрузкой

- Загрузка из Kafka и расчёт raw/ods/dm — через задачи DAG (Spark).
- Загрузка справочников из Postgres, обновление витрин — добавляются новыми задачами в DAG или отдельными DAG-ами по мере расширения.
