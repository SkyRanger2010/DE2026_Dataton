# Airflow: эксплуатация

## Зависимости перед запуском DAG

1. **Postgres** — доступна, миграции выполнены (airflow-init).
2. **Spark:** контейнеры **spark-master** и **spark-worker** в состоянии running. Без воркера spark-submit зависнет в ожидании ресурсов.
3. **Kafka** (для kafka_to_raw): топик `banner_events` создан; при отсутствии данных задача может завершиться с пустой таблицей или таймаутом — в зависимости от логики скрипта.
4. **MinIO, Hive Metastore** — для записи в Iceberg; minio-init должен создать бакет `warehouse`.

## Типичные сбои

| Симптом | Возможная причина | Действие |
|--------|-------------------|----------|
| Task failed: Container spark-master not found | Контейнер не запущен или другое имя | `docker compose ps`, поднять spark-master/spark-worker |
| spark-submit failed, exit code 1 | Ошибка в скрипте или окружении (Ivy, класс) | Смотреть лог задачи в Airflow; проверить скрипт локально через `docker compose exec spark-master ... spark-submit ...` |
| Ivy cache / permission denied | Нет прав на `/home/spark/.ivy2` в контейнере | В DAG уже есть `mkdir -p` перед запуском; убедиться, что том `spark_ivy_cache` смонтирован (docker-compose) |
| Connection refused to hive-metastore:9083 | Hive Metastore не поднят или не в одной сети | Проверить hive-metastore, сеть `dataton` |

## Ручной запуск шага ETL без Airflow

Для отладки можно выполнить тот же spark-submit из хоста:

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/raw_to_ods.py
```

Список всех команд — в [spark/README.md](../spark/README.md) и [spark/scripts/README.md](../spark/scripts/README.md).

## Логи

- **Задача Airflow:** в UI — кнопка «Log» у задачи.
- **Spark:** вывод spark-submit попадает в лог задачи Airflow (stdout/stderr от exec_run).

## Добавление нового DAG

1. Создайте файл `airflow/dags/имя_dag.py` с декоратором `@dag` и функциями с `@task`.
2. Убедитесь, что синтаксис корректен (при необходимости `python -m py_compile airflow/dags/имя_dag.py`).
3. Перезапуск не обязателен: scheduler подхватывает изменения в каталоге dags с интервалом (по умолчанию ~30 с).
4. В UI появится новый DAG; включите его (Unpause) при необходимости.

## Алерты в Telegram

По архитектуре предусмотрены уведомления при падении задач. Настройка: в `default_args` DAG добавить `on_failure_callback`, вызывающий отправку в Telegram (например через Bot API). Токен и chat_id хранить в Airflow Variables или в переменных окружения контейнера, не в коде.
