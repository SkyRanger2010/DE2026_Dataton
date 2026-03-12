"""
Перенос из raw в ODS с правилами аналитики: выкидываем NULL по user_id, дедупликация, приведение типов и расчёт CPM/CPC по кампаниям.
Используется в CSV-потоке после csv_to_raw_iceberg. Запуск — DAG csv_pipeline или spark-submit.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number, when, regexp_replace, to_date, count as spark_count, sum as spark_sum
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.sql.window import Window


def main():
    spark = SparkSession.builder.getOrCreate()
    spark.sql("CREATE DATABASE IF NOT EXISTS ods")

    # Показы баннеров: очистка и дедупликация
    df = spark.table("spark_catalog.raw.fct_banners_show")
    df = df.withColumn("is_clicked", col("is_clicked").cast(IntegerType()))
    df = df.filter(col("user_id").isNotNull())
    w = Window.partitionBy("banner_id", "user_id", "event_timestamp").orderBy("event_timestamp")
    df = df.withColumn("rn", row_number().over(w)).filter(col("rn") == 1).drop("rn")
    df.writeTo("spark_catalog.ods.fct_banners").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.fct_banners OK")
    df_banners = df

    # Установки
    df = spark.table("spark_catalog.raw.installs").filter(col("user_id").isNotNull())
    df.writeTo("spark_catalog.ods.installs").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.installs OK")

    # Действия пользователей
    df = spark.table("spark_catalog.raw.fct_actions").filter(col("user_id").isNotNull())
    df.writeTo("spark_catalog.ods.fct_actions").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.fct_actions OK")

    # Справочник баннеров
    df = spark.table("spark_catalog.raw.cd_banner").dropDuplicates(["banner_id"])
    df.writeTo("spark_catalog.ods.cd_banner").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.cd_banner OK")

    # Кампании с расчётом CPM/CPC по агрегатам показов
    df_camp = spark.table("spark_catalog.raw.cd_campaign")
    df_camp = df_camp.withColumn("daily_budget", regexp_replace(col("daily_budget"), ",", ".").cast(DoubleType()))
    df_camp = df_camp.withColumn("start_date", to_date(col("start_date"), "dd.MM.yyyy"))
    df_camp = df_camp.withColumn("end_date", to_date(col("end_date"), "dd.MM.yyyy"))
    stats = df_banners.groupBy("campaign_id").agg(
        spark_count("*").alias("impressions"),
        spark_sum("is_clicked").alias("clicks"),
    )
    df_camp = df_camp.join(stats, "campaign_id", "left")
    df_camp = df_camp.withColumn("impressions", when(col("impressions").isNull(), 0).otherwise(col("impressions").cast("long")))
    df_camp = df_camp.withColumn("clicks", when(col("clicks").isNull(), 0).otherwise(col("clicks").cast("long")))
    df_camp = df_camp.withColumn(
        "calculated_cpm",
        when(col("impressions") > 0, (col("daily_budget") * 1000 / col("impressions")).cast(DoubleType())).otherwise(0.0)
    ).withColumn(
        "calculated_cpc",
        when(col("clicks") > 0, (col("daily_budget") / col("clicks")).cast(DoubleType())).otherwise(0.0)
    )
    df_camp = df_camp.dropDuplicates(["campaign_id"])
    df_camp.writeTo("spark_catalog.ods.cd_campaign").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.cd_campaign OK")

    # Справочник пользователей
    df = spark.table("spark_catalog.raw.cd_user").filter(col("user_id").isNotNull())
    df = df.withColumn("date_create", to_date(col("date_create")))
    df = df.withColumn("date_end", to_date(col("date_end")))
    df.writeTo("spark_catalog.ods.cd_user").using("iceberg").tableProperty("format-version", "2").createOrReplace()
    print("ods.cd_user OK")

    print("ODS обновлён из raw по правилам качества.")


if __name__ == "__main__":
    main()
