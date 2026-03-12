"""
Чтение топика banner_events из Kafka и запись в raw.banner_events (Iceberg).
Батч-режим: забираем накопленные сообщения, парсим JSON, добавляем event_date и пишем в каталог raw.
Запуск из контейнера spark-master: см. spark/README.md или DAG banner_events_pipeline.
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, to_date
from pyspark.sql.types import LongType, StringType, IntegerType, StructType, StructField

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.environ.get("BANNER_EVENTS_TOPIC", "banner_events")


def main():
    spark = SparkSession.builder.getOrCreate()

    kafka_df = (
        spark.read.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    schema = StructType([
        StructField("event_id", StringType()),
        StructField("banner_id", LongType()),
        StructField("campaign_id", LongType()),
        StructField("user_id", LongType()),
        StructField("event_ts", StringType()),
        StructField("placement", StringType()),
        StructField("device_type", StringType()),
        StructField("os", StringType()),
        StructField("geo", StringType()),
        StructField("is_clicked", IntegerType()),
    ])

    df = (
        kafka_df.select(from_json(col("value").cast("string"), schema).alias("v"))
        .select("v.*")
        .withColumn("event_ts", to_timestamp(col("event_ts")))
        .withColumn("event_date", to_date(col("event_ts")))
    )

    if df.isEmpty():
        print("No records from Kafka, skipping write")
        return

    spark.sql("CREATE DATABASE IF NOT EXISTS raw")

    # Перезаписываем raw-таблицу по партиции даты (MVP — полное обновление батча)
    df.writeTo("spark_catalog.raw.banner_events").using("iceberg").tableProperty("format-version", "2").partitionedBy(col("event_date")).createOrReplace()
    print("Wrote to raw.banner_events")


if __name__ == "__main__":
    main()
