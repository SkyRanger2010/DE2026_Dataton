#!/usr/bin/env bash
# Создание топиков Kafka для DE2026_Dataton.
# Запуск из корня репо после docker compose up: ./kafka/create_topic.sh

set -e
PARTITIONS="${PARTITIONS:-6}"
REPLICATION="${REPLICATION:-1}"

# События/сырые данные: Spark kafka_to_raw, producer_simulate
# raw_actions — Debezium CDC (ods.fct_actions) → Iceberg Sink
# control-iceberg — управление коммитами Iceberg Sink Connector
# filebeat-logs — Filebeat (профиль filebeat)
TOPICS="banner_events installs actions raw_actions control-iceberg filebeat-logs"

if command -v docker >/dev/null 2>&1 && docker compose exec kafka true 2>/dev/null; then
  for TOPIC in $TOPICS; do
    docker compose exec kafka kafka-topics --create \
      --bootstrap-server localhost:9092 \
      --topic "$TOPIC" \
      --partitions "$PARTITIONS" \
      --replication-factor "$REPLICATION" \
      --if-not-exists
    echo "Topic $TOPIC OK"
  done
  echo "Готово. Список: docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092"
else
  echo "Запустите из корня проекта при поднятом стеке: docker compose up -d"
  echo "Пример вручную:"
  echo "  docker compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic banner_events --partitions $PARTITIONS --replication-factor $REPLICATION --if-not-exists"
  exit 1
fi
