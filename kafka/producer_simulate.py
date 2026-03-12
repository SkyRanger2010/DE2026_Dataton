#!/usr/bin/env python3
"""
Симуляция потока событий баннеров в топик banner_events для тестов и демо.
Нужен kafka-python. Запуск: python kafka/producer_simulate.py [--count 1000] [--bootstrap kafka:9092]
"""
import argparse
import json
import random
import time
import uuid
from datetime import datetime, timedelta

try:
    from kafka import KafkaProducer
except ImportError:
    raise SystemExit("Install: pip install kafka-python")


def main():
    p = argparse.ArgumentParser(description="Produce banner_events to Kafka")
    p.add_argument("--bootstrap", default="localhost:9092", help="Kafka bootstrap servers")
    p.add_argument("--topic", default="banner_events", help="Topic name")
    p.add_argument("--count", type=int, default=100, help="Number of events to send")
    p.add_argument("--delay", type=float, default=0.05, help="Delay between messages (sec)")
    args = p.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap.split(","),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    placements = ["site", "app", "social"]
    devices = ["phone", "tablet"]
    oses = ["ios", "android"]
    geos = ["Москва", "Санкт-Петербург", "Казань", "Самара", "Екатеринбург"]

    base_ts = datetime.utcnow() - timedelta(days=1)
    for i in range(args.count):
        event_ts = base_ts + timedelta(seconds=i * 10)
        event = {
            "event_id": str(uuid.uuid4()),
            "banner_id": random.randint(1, 15),
            "campaign_id": random.randint(1, 3),
            "user_id": random.randint(1, 100000),
            "event_ts": event_ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "placement": random.choice(placements),
            "device_type": random.choice(devices),
            "os": random.choice(oses),
            "geo": random.choice(geos),
            "is_clicked": 1 if random.random() < 0.1 else 0,
        }
        producer.send(args.topic, value=event)
        if args.delay:
            time.sleep(args.delay)
    producer.flush()
    print(f"Sent {args.count} events to {args.topic}")


if __name__ == "__main__":
    main()
