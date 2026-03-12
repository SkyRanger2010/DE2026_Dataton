"""
Ежедневное обновление витрины признаков для ML: ods.banner_events → ml.user_features.
Запускается после наполнения ODS (banner_events или fct_banners). Дальше по цепочке — обучение и инференс (вне DAG или отдельной задачей).
"""
from datetime import datetime

from airflow.decorators import dag, task

from spark_runner import run_spark_script, PACKAGES_ICEBERG


@dag(
    dag_id="ml_daily_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["ml", "features", "user_features"],
    default_args={"retries": 2},
)
def ml_daily_pipeline():
    @task
    def build_user_features():
        run_spark_script("build_ml_user_features.py", PACKAGES_ICEBERG)

    build_user_features()


ml_daily_pipeline()
