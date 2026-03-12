"""
Нормализация сырых событий баннеров: убираем записи без user_id и дубликаты по (banner_id, user_id, event_ts).
Результат пишем в ods.banner_events. Запуск через spark-submit или DAG banner_events_pipeline.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


def main():
    spark = SparkSession.builder.getOrCreate()

    df = spark.table("spark_catalog.raw.banner_events")
    df = df.filter("user_id IS NOT NULL")
    df = df.dropDuplicates(["banner_id", "user_id", "event_ts"])

    if df.isEmpty():
        print("No records after cleanup, skipping write")
        return

    spark.sql("CREATE DATABASE IF NOT EXISTS ods")
    # Полное обновление ODS по партиции event_date
    df.writeTo("spark_catalog.ods.banner_events").using("iceberg").tableProperty("format-version", "2").partitionedBy(col("event_date")).createOrReplace()
    print("Wrote to ods.banner_events")


if __name__ == "__main__":
    main()
