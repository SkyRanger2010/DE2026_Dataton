"""
Пакетный инференс: по витрине признаков и обученной модели считаем вероятность клика и рекомендуем ставку (high_spend +20%, low_active стандарт).
Результат — Parquet; при необходимости можно дописать выгрузку в Iceberg ml.click_predictions.
"""
import argparse
import json
from pathlib import Path
from datetime import date

import pandas as pd
import xgboost as xgb


# Должны совпадать с признаками при обучении (без clicks_7d)
FEATURE_COLS = [
    "impressions_7d",
    "actions_7d",
    "recency_days",
    "device_type",
    "os",
]
CAT_COLS = ["device_type", "os", "segment", "tariff"]

# Правила recommend_bid по сегменту (аналитик BI / архитектура)
RECOMMEND_BID_RULES = {
    "high_spend": "+20%",
    "low_active": "стандарт",
    "default": "стандарт",
}


def load_features(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if p.suffix.lower() in (".csv", ".csv.gz"):
        return pd.read_csv(path)
    raise ValueError(f"Unsupported format: {p.suffix}")


def prepare_df(df: pd.DataFrame, meta: dict):
    df = df.copy()
    use_cols = meta.get("feature_columns", [c for c in FEATURE_COLS + CAT_COLS if c in df.columns])
    for c in use_cols:
        if c in df.columns and df[c].dtype.name == "object":
            df[c] = df[c].fillna("__null__").astype("category").cat.codes
    keep = ["user_id", "snapshot_date"] + [c for c in use_cols if c in df.columns]
    if "segment" in df.columns:
        keep.append("segment")
    return df[keep], use_cols


def recommend_bid(segment: str, probability_click: float) -> str:
    if pd.isna(segment):
        segment = "default"
    seg = str(segment).strip().lower()
    if "high" in seg or "spend" in seg or probability_click >= 0.5:
        return "high_spend +20%"
    if "low" in seg or "active" in seg:
        return "low_active стандарт"
    return RECOMMEND_BID_RULES.get(seg, RECOMMEND_BID_RULES["default"])


def main():
    parser = argparse.ArgumentParser(description="Batch inference: probability_click, recommend_bid")
    parser.add_argument("--features-path", type=str, default="ml/data/user_features.parquet")
    parser.add_argument("--model-path", type=str, default="ml/models/xgb_ctr.json")
    parser.add_argument("--output-path", type=str, default="ml/data/click_predictions.parquet")
    parser.add_argument("--snapshot-date", type=str, default=None)
    args = parser.parse_args()

    df = load_features(args.features_path)
    if "snapshot_date" not in df.columns and args.snapshot_date:
        df["snapshot_date"] = pd.to_datetime(args.snapshot_date).date()
    elif "snapshot_date" not in df.columns:
        df["snapshot_date"] = date.today()

    meta_path = args.model_path.replace(".json", "_meta.json")
    meta = {}
    if Path(meta_path).exists():
        with open(meta_path) as f:
            meta = json.load(f)

    df_prep, use_cols = prepare_df(df, meta)
    X = df_prep[use_cols].fillna(0)

    model = xgb.XGBClassifier()
    model.load_model(args.model_path)
    proba = model.predict_proba(X)[:, 1]

    out = pd.DataFrame({
        "user_id": df_prep["user_id"],
        "snapshot_date": df_prep["snapshot_date"],
        "probability_click": proba,
        "segment": df_prep["segment"].fillna("default") if "segment" in df_prep.columns else "default",
    })
    out["recommend_bid"] = out.apply(
        lambda r: recommend_bid(r["segment"], r["probability_click"]), axis=1
    )

    Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(args.output_path, index=False)
    print(f"Predictions saved: {args.output_path}, rows={len(out)}")


if __name__ == "__main__":
    main()
