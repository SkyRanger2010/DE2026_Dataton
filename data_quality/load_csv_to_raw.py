"""
Загрузка CSV из sample_data в схему raw в PostgreSQL (raw — в БД, не в папке).
Запуск: из корня репозитория при поднятом Postgres стека
  python data_quality/load_csv_to_raw.py
  или с переменными: POSTGRES_HOST=postgres POSTGRES_DB=airflow python data_quality/load_csv_to_raw.py
"""
import os
import sys
import csv
import re
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    try:
        import psycopg
        psycopg2 = None
    except ImportError:
        raise SystemExit("Установите psycopg2: pip install psycopg2-binary")

# Корень репо: скрипт в data_quality/, данные в sample_data/
REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "sample_data"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")


def clean_name(name):
    s = re.sub(r"[^\w]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"


def conn():
    if psycopg2:
        return psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
    return psycopg.connect(
        f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
    )


def load_csv(path, delimiter=";", encoding="utf-8"):
    with open(path, encoding=encoding, newline="") as f:
        r = csv.reader(f, delimiter=delimiter)
        header = [clean_name(h) for h in next(r)]
        rows = list(r)
    return header, rows


def main():
    if not SAMPLE_DATA.exists():
        print(f"Папка не найдена: {SAMPLE_DATA}")
        sys.exit(1)
    print("Подключение к Postgres...")
    conn_obj = conn()
    conn_obj.autocommit = False
    cur = conn_obj.cursor()
    try:
        # Fct_banners_show — крупная таблица, батчами
        print("Загрузка raw.fct_banners_show...")
        path = SAMPLE_DATA / "Fct_banners_show.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.fct_banners_show")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            def ts_parse(s):
                if not s:
                    return None
                s = s.strip().replace(" ", "T")
                return s if s else None
            batch = []
            for r in rows:
                if len(r) < 9:
                    continue
                try:
                    batch.append((
                        r[idx.get("banner_id", 0)],
                        r[idx.get("campaign_id", 1)],
                        r[idx.get("user_id", 2)],
                        ts_parse(r[idx.get("timestamp", 3)]),
                        r[idx.get("placement_сайт_приложение_соцсеть", 4)] if len(r) > 4 else None,
                        r[idx.get("device_type", 5)] if len(r) > 5 else None,
                        r[idx.get("os", 6)] if len(r) > 6 else None,
                        r[idx.get("geo", 7)] if len(r) > 7 else None,
                        int(r[idx.get("is_clicked_0_1", 8)]) if len(r) > 8 and str(r[idx.get("is_clicked_0_1", 8)]).strip().isdigit() else None,
                    ))
                except (ValueError, IndexError):
                    continue
                if len(batch) >= 5000:
                    execute_values(cur, "INSERT INTO raw.fct_banners_show (banner_id, campaign_id, user_id, event_timestamp, placement, device_type, os, geo, is_clicked) VALUES %s", batch, page_size=1000)
                    conn_obj.commit()
                    batch = []
            if batch:
                execute_values(cur, "INSERT INTO raw.fct_banners_show (banner_id, campaign_id, user_id, event_timestamp, placement, device_type, os, geo, is_clicked) VALUES %s", batch, page_size=1000)
            print(f"  Загружено строк: {len(rows)}")
        else:
            print(f"  Файл не найден: {path}")

        # Installs
        print("Загрузка raw.installs...")
        path = SAMPLE_DATA / "Installs.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.installs")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            for r in rows:
                if len(r) < 2:
                    continue
                cur.execute(
                    "INSERT INTO raw.installs (user_id, install_timestamp, source) VALUES (%s, %s::timestamp, %s)",
                    (r[idx.get("user_id", 0)], r[idx.get("install_timestamp", 1)].strip().replace(" ", "T") if len(r) > 1 else None, r[idx.get("source_баннер_органика_другое", 2)] if len(r) > 2 else None)
                )
            conn_obj.commit()
            print(f"  Загружено строк: {len(rows)}")

        # Fct_actions
        print("Загрузка raw.fct_actions...")
        path = SAMPLE_DATA / "Fct_actions.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.fct_actions")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            for r in rows:
                if len(r) < 2:
                    continue
                cur.execute(
                    "INSERT INTO raw.fct_actions (user_id, session_start, actions) VALUES (%s, %s::timestamp, %s)",
                    (r[idx.get("user_id", 0)], r[idx.get("session_start", 1)].strip().replace(" ", "T") if len(r) > 1 else None, r[idx.get("actions_регистрация_первый_заказ_и_т_д", 2)] if len(r) > 2 else None)
                )
            conn_obj.commit()
            print(f"  Загружено строк: {len(rows)}")

        # CD_banner
        print("Загрузка raw.cd_banner...")
        path = SAMPLE_DATA / "CD_banner.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.cd_banner")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            for r in rows:
                if len(r) < 5:
                    continue
                cur.execute(
                    "INSERT INTO raw.cd_banner (banner_id, creative_type, message, size, target_audience_segment) VALUES (%s,%s,%s,%s,%s)",
                    (r[idx.get("banner_id", 0)], r[idx.get("creative_type_статика_видео_анимация", 1)] if len(r) > 1 else None, r[idx.get("message_сообщение_на_баннере", 2)] if len(r) > 2 else None, r[idx.get("size", 3)] if len(r) > 3 else None, r[idx.get("target_audience_segment", 4)] if len(r) > 4 else None)
                )
            conn_obj.commit()
            print(f"  Загружено строк: {len(rows)}")

        # CD_campaign
        print("Загрузка raw.cd_campaign...")
        path = SAMPLE_DATA / "CD_campaign.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.cd_campaign")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            for r in rows:
                if len(r) < 5:
                    continue
                cur.execute(
                    "INSERT INTO raw.cd_campaign (campaign_id, daily_budget, start_date, end_date) VALUES (%s,%s,%s,%s)",
                    (r[idx.get("campaign_id", 0)], r[idx.get("daily_budget", 1)], r[idx.get("start_date", 2)], r[idx.get("end_date", 3)])
                )
            conn_obj.commit()
            print(f"  Загружено строк: {len(rows)}")

        # CD_user
        print("Загрузка raw.cd_user...")
        path = SAMPLE_DATA / "CD_user.csv"
        if path.exists():
            header, rows = load_csv(path)
            cur.execute("TRUNCATE TABLE raw.cd_user")
            idx = {clean_name(h): i for i, h in enumerate(header)}
            for r in rows:
                if len(r) < 3:
                    continue
                cur.execute(
                    "INSERT INTO raw.cd_user (user_id, segment, tariff, date_create, date_end) VALUES (%s,%s,%s,%s,%s)",
                    (r[idx.get("User_id", 0)], r[idx.get("segment", 1)] if len(r) > 1 else None, r[idx.get("tariff", 2)] if len(r) > 2 else None, r[idx.get("date_create", 3)] if len(r) > 3 else None, r[idx.get("date_end", 4)] if len(r) > 4 else None)
                )
            conn_obj.commit()
            print(f"  Загружено строк: {len(rows)}")

        conn_obj.commit()
        print("Готово: raw заполнен из CSV.")
    except Exception as e:
        conn_obj.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        cur.close()
        conn_obj.close()


if __name__ == "__main__":
    main()
