# apache/hive:4.0.0 + PostgreSQL JDBC driver (для метастора на Postgres)
FROM apache/hive:4.0.0
USER root
# Скачивание через ADD (в образе нет curl/wget)
ADD --chown=hive:hive https://jdbc.postgresql.org/download/postgresql-42.7.3.jar /opt/hive/lib/postgres.jar
USER hive
