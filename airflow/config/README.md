# Конфигурация Airflow (инженер Airflow)

## Где задаётся конфиг

- **docker-compose:** сервисы `airflow-webserver`, `airflow-scheduler` — переменные окружения (Postgres, Redis, Fernet key). Монтирование: `./airflow/dags:/opt/airflow/dags`, `/var/run/docker.sock` для запуска Spark.
- **Образ:** `apache/airflow:2.10.3-python3.11`, дополнительно ставится `docker` (_PIP_ADDITIONAL_REQUIREMENTS).

## Подключения (Connections)

В MVP явные Connection в Airflow не используются: Spark запускается через Docker API по имени контейнера. При необходимости добавить:

- **Trino** — для SQL-операторов или проверок (host: trino, port 8080, extra `{"catalog": "iceberg"}`).
- **Postgres** — для метаданных уже задан через `SQLALCHEMY_DATABASE_URI`; отдельный Connection может понадобиться для задач типа «проверка в БД».

Создание: **Admin → Connections → +**.

## Переменные (Variables)

Сейчас константы (имя контейнера Spark, URL мастера, пути) захардкожены в DAG. При переносе в разные окружения можно вынести в **Admin → Variables**, например:

| Key | Пример | Назначение |
|-----|--------|------------|
| spark_master_container | spark-master | Имя/префикс контейнера для exec |
| spark_master_url | spark://spark-master:7077 | URL мастера Spark |
| spark_app_base | /opt/spark/app/scripts | Базовый путь к скриптам в контейнере |

В коде DAG: `Variable.get("spark_master_container", default_var="spark-master")`.

## Retry и алерты

- **Retry:** в DAG задано `default_args={"retries": 2}`. Полные default_args при необходимости: `retries=2`, `retry_delay=timedelta(minutes=5)`, `on_failure_callback=...`.
- **Алерты в Telegram:** по архитектуре предусмотрены; для включения нужно задать Connection типа `telegram` (bot token) и в default_args указать `on_failure_callback` с отправкой сообщения (например через оператор или свой callback).

## Запуск и проверка

- **Web UI:** http://localhost:8080 (логин/пароль — задаются при `airflow fab create-admin`).
- **Включение DAG:** по умолчанию новые DAG-и в паузе; переключите тумблер «Unpause» для `banner_events_pipeline`.
- **Ручной запуск:** Trigger DAG. Убедитесь, что контейнеры spark-master и spark-worker запущены и доступны из сети Airflow.
