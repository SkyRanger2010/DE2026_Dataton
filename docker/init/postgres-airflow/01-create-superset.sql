-- БД для Superset (тот же хост и пользователь, что для Airflow)
CREATE DATABASE superset;
GRANT ALL PRIVILEGES ON DATABASE superset TO airflow;
