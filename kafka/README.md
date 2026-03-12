# Kafka

Потоковый сбор и буферизация событий.

- **Брокеры:** в Docker Compose — 1 брокер (MVP); репликация 1.
- **Топики (MVP):** `banner_events` — события показов/кликов по баннерам.
- Полная версия: `installs`, `actions`; 12 партиций, `acks=all`.

См. [Архитектура](../docs/ARCHITECTURE.md).

## MVP: создание топика и симуляция потока

### Создание топика

После запуска стека (`docker compose up -d`) выполните из корня репозитория:

```bash
# через скрипт (требует docker compose)
chmod +x kafka/create_topic.sh
./kafka/create_topic.sh
```

Или вручную:

```bash
docker compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic banner_events \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists
```

### Продюсер для симуляции

Скрипт шлёт в `banner_events` JSON-сообщения в формате raw.banner_events (event_id, banner_id, campaign_id, user_id, event_ts, placement, device_type, os, geo, is_clicked).

**Зависимость:** `pip install kafka-python`

**Запуск с хоста:** брокер доступен на **localhost:29092** (внутри Docker контейнеры используют kafka:9092). По умолчанию скрипт подключается к `localhost:9092`; для доступа с хоста укажите `--bootstrap localhost:29092`:

```bash
python kafka/producer_simulate.py
python kafka/producer_simulate.py --bootstrap localhost:29092 --count 1000 --delay 0.02
```

**Запуск из контейнера в сети dataton** (если продюсер в Docker):

```bash
docker compose run --rm -e KAFKA_BOOTSTRAP=kafka:9092 python:3.11-slim bash -c "pip install kafka-python && python -c \"exec(open('kafka/producer_simulate.py').read()); main()\""
```

Или смонтировать проект и вызвать: `--bootstrap kafka:9092` при запуске из контейнера в той же сети.

---

## Kafka Connect, Debezium и Iceberg Sink 

В стек добавлены **Kafka Connect** (Debezium) и **Kafka UI**. Опционально — **Filebeat** для отправки файловых логов/CSV в Kafka.

### Kafka Connect (порт 8083)

- **Образ:** `quay.io/debezium/connect:2.7` — уже содержит Debezium Postgres Connector.
- **Плагины:** каталог `kafka/connect-plugins/` смонтирован в контейнер. Для **Iceberg Sink** нужно скачать JAR коннектора (например [iceberg-kafka-connect](https://github.com/apache/iceberg/blob/master/connect/README.md)) и положить в `kafka/connect-plugins/`, затем перезапустить `kafka-connect`.

### Регистрация коннекторов

Конфиги лежат в `kafka/connectors_settings/`:

1. **Debezium (CDC Postgres → Kafka)**  
   Читает изменения из `ods.fct_actions` в Postgres и пишет в топик `raw_actions`:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     --data @kafka/connectors_settings/debezium-postgres-ods.json \
     http://localhost:8083/connectors
   ```

2. **Iceberg Sink (Kafka → Iceberg)**  
   Пишет из топика `raw_actions` в таблицу Iceberg `ods.fct_actions` (каталог Hadoop, warehouse в MinIO). Таблицу нужно создать заранее (например через Spark/Trino). В конфиге убраны комментарии (JSON без `//`):
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     --data @kafka/connectors_settings/iceberg-sink-raw_actions.json \
     http://localhost:8083/connectors
   ```

Для CDC в Postgres включены `wal_level=logical` и публикация `dbz_publication` для `ods.fct_actions` (см. `docker/init/postgres/03-cdc-publication.sql`).

### Kafka UI (порт 8090)

- **URL:** http://localhost:8090  
- Кластер: `dataton`, брокеры `kafka:9092`. Просмотр топиков, consumer groups, сообщений.

### Filebeat (профиль `filebeat`)

Отправка файлов (например CSV из `sample_data`) в Kafka как сырые строки.

- **Запуск:** `docker compose --profile filebeat up -d` (вместе с основным стеком).
- **Конфиг:** `kafka/filebeat/filebeat.yml`. По умолчанию читает `/logs/*.csv` (в compose смонтирован `./sample_data` как `/logs`), топик — `filebeat-logs`.
- Для событий баннеров в формате MVP удобнее использовать `kafka/producer_simulate.py` (JSON в `banner_events`); Filebeat подходит для произвольных логов/файлов.

## Устранение неполадок

- **Kafka Connect: «kafka: Name or service not known» / «No resolvable bootstrap urls»** — Connect не может разрешить хост `kafka`. Запускайте весь стек из корня: `docker compose up -d` (не только `kafka-connect`). В compose для Kafka включён healthcheck, для Connect задано `depends_on: kafka: condition: service_healthy` и `restart: on-failure` — после перезапуска (`docker compose up -d`) Connect должен стартовать после готовности брокера. Если ошибка сохраняется (например на WSL2), дайте сети и DNS стабилизироваться и выполните `docker compose restart kafka-connect`.


