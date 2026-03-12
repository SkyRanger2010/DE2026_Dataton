"""
Агрегация событий баннеров по кампании и дню: показы, клики, CTR.
Витрина dm.campaign_daily для BI (дашборды Superset). Запуск — через DAG или spark-submit.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum, when, current_date, lit


def main():
    spark = SparkSession.builder.getOrCreate()

    df = spark.table("spark_catalog.ods.banner_events")
    df = df.withColumn("date", col("event_date"))

    agg = (
        df.groupBy("campaign_id", "date")
        .agg(
            count("*").alias("impressions"),
            spark_sum("is_clicked").alias("clicks"),
        )
        .withColumn("ctr", when(col("impressions") > 0, col("clicks") / col("impressions")).otherwise(0.0))
        .withColumn("installs", lit(0).cast("long"))
        .withColumn("conversions", lit(0).cast("long"))
        .withColumn("revenue", lit(0.0))
        .withColumn("cpc", lit(0.0))
        .withColumn("cpm", lit(0.0))
        .withColumn("conversion_rate", lit(0.0))
        .withColumn("processing_date", current_date())
    )

    spark.sql("CREATE DATABASE IF NOT EXISTS dm")
    agg.writeTo("spark_catalog.dm.campaign_daily").using("iceberg").tableProperty("format-version", "2").partitionedBy(col("date")).createOrReplace()
    print("Wrote to dm.campaign_daily")


if __name__ == "__main__":
    main()
