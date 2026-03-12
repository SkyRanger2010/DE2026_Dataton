CREATE DATABASE superset;
CREATE DATABASE hivemeta;
-- доступ для Airflow-пользователя к БД Superset (тот же пользователь в compose)
GRANT ALL PRIVILEGES ON DATABASE superset TO airflow;
