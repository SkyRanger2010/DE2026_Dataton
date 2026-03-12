"""
Сборка витрины признаков для модели прогноза клика: показы/клики за 7 дней, recency, device_type, os.
Читает ods.banner_events; при появлении ods.fct_actions и ods.cd_user можно добавить actions_7d, segment, tariff.
Аргумент --snapshot-date YYYY-MM-DD опционален (по умолчанию — сегодня).
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum, max as spark_max, datediff, lit
from datetime import datetime, timedelta
import sys


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    spark = SparkSession.builder.getOrCreate()

    snapshot_date = datetime.now().date()
    for i, arg in enumerate(sys.argv):
        if arg == "--snapshot-date" and i + 1 < len(sys.argv):
            snapshot_date = parse_date(sys.argv[i + 1])
            break

    df = spark.table("spark_catalog.ods.banner_events")
    df = df.withColumn("event_date", col("event_ts").cast("date"))

    # Скользящее окно 7 дней до даты среза
    date_from = snapshot_date - timedelta(days=7)
    df_window = df.filter(
        (col("event_date") >= lit(date_from)) & (col("event_date") < lit(snapshot_date))
    )

    # Агрегация по пользователю
    user_agg = df_window.groupBy("user_id").agg(
        count("*").alias("impressions_7d"),
        spark_sum("is_clicked").alias("clicks_7d"),
        spark_max("event_ts").alias("last_event_ts"),
        spark_max("device_type").alias("device_type"),
        spark_max("os").alias("os"),
    )
    user_agg = user_agg.withColumn(
        "recency_days",
        datediff(lit(snapshot_date), col("last_event_ts").cast("date")),
    ).drop("last_event_ts")

    # Пока без join с actions и cd_user — подставляем заглушки
    user_agg = user_agg.withColumn("actions_7d", lit(0).cast("long"))
    user_agg = user_agg.withColumn("segment", lit(None).cast("string"))
    user_agg = user_agg.withColumn("tariff", lit(None).cast("string"))

    # TODO: подключить ods.fct_actions и ods.cd_user для actions_7d, segment, tariff

    user_agg = user_agg.withColumn("snapshot_date", lit(snapshot_date))

    spark.sql("CREATE DATABASE IF NOT EXISTS ml")
    user_agg.writeTo("spark_catalog.ml.user_features").using("iceberg") \
        .tableProperty("format-version", "2") \
        .partitionedBy(col("snapshot_date")) \
        .createOrReplace()
    print(f"Wrote ml.user_features for snapshot_date={snapshot_date}")


if __name__ == "__main__":
    main()
