"""
Витрина dm.campaign_daily с полным набором метрик: показы, клики, установки, конверсии, revenue, CTR, CPC, CPM.
Используется в CSV-потоке после raw_to_ods_iceberg. Логика сверена с эталонным SQL аналитика BI.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, countDistinct, sum as spark_sum,
    when, round as spark_round, current_date, to_date,
)
from pyspark.sql.types import DoubleType


def main():
    spark = SparkSession.builder.getOrCreate()

    # Агрегаты по кампании и дню: показы и клики
    df_banners = spark.table("spark_catalog.ods.fct_banners").withColumn(
        "date", to_date(col("event_timestamp"))
    )
    daily_banners = df_banners.groupBy("date", "campaign_id").agg(
        count("*").alias("impressions"),
        spark_sum("is_clicked").alias("clicks"),
    )

    # Установки по дню и кампании (через связку user_id + дата с fct_banners)
    df_installs = spark.table("spark_catalog.ods.installs").withColumn(
        "date", to_date(col("install_timestamp"))
    )
    banner_dates = df_banners.select("user_id", "date", "campaign_id").distinct()
    installs_with_campaign = df_installs.join(
        banner_dates,
        (df_installs["user_id"] == banner_dates["user_id"]) & (df_installs["date"] == banner_dates["date"]),
        "inner",
    )
    daily_installs = installs_with_campaign.groupBy("date", "campaign_id").agg(
        countDistinct("user_id").alias("installs"),
    )

    # Действия: конверсии и revenue по правилам аналитика
    df_actions = spark.table("spark_catalog.ods.fct_actions").filter(
        col("actions").isNotNull() & (col("actions") != "")
    ).withColumn("date", to_date(col("session_start")))
    actions_with_campaign = df_actions.join(
        banner_dates,
        (df_actions["user_id"] == banner_dates["user_id"]) & (df_actions["date"] == banner_dates["date"]),
        "inner",
    )
    revenue_expr = when(col("actions") == "first_order", 100) \
        .when(col("actions") == "tarrif_switch", 50) \
        .when(col("actions") == "registration", 10) \
        .otherwise(0)
    daily_actions = actions_with_campaign.withColumn("revenue_val", revenue_expr).groupBy("date", "campaign_id").agg(
        countDistinct("user_id").alias("conversions"),
        spark_sum("revenue_val").alias("revenue"),
    )

    # Сводим в одну витрину: full outer join по (date, campaign_id)
    dm = daily_banners.join(daily_installs, ["date", "campaign_id"], "full") \
        .join(daily_actions, ["date", "campaign_id"], "full")

    dm = dm.select(
        col("date"),
        col("campaign_id").cast("long").alias("campaign_id"),
        when(col("impressions").isNull(), 0).otherwise(col("impressions").cast("long")).alias("impressions"),
        when(col("clicks").isNull(), 0).otherwise(col("clicks").cast("long")).alias("clicks"),
        when(col("installs").isNull(), 0).otherwise(col("installs").cast("long")).alias("installs"),
        when(col("conversions").isNull(), 0).otherwise(col("conversions").cast("long")).alias("conversions"),
        when(col("revenue").isNull(), 0.0).otherwise(col("revenue").cast(DoubleType())).alias("revenue"),
        when(col("impressions") > 0, spark_round(col("clicks").cast("double") / col("impressions") * 100, 4)).otherwise(0.0).alias("ctr"),
        when(col("clicks") > 0, spark_round(col("revenue").cast("double") / col("clicks"), 2)).otherwise(0.0).alias("cpc"),
        when(col("impressions") > 0, spark_round(col("revenue").cast("double") / col("impressions") * 1000, 2)).otherwise(0.0).alias("cpm"),
        when(col("clicks") > 0, spark_round(col("installs").cast("double") / col("clicks") * 100, 4)).otherwise(0.0).alias("conversion_rate"),
        current_date().alias("processing_date"),
    )

    spark.sql("CREATE DATABASE IF NOT EXISTS dm")
    dm.writeTo("spark_catalog.dm.campaign_daily").using("iceberg") \
        .tableProperty("format-version", "2") \
        .partitionedBy(col("date")) \
        .createOrReplace()
    print("Wrote dm.campaign_daily (full metrics from ODS)")


if __name__ == "__main__":
    main()
