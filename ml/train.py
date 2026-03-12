"""
Обучение модели XGBoost на витрине признаков: цель — прогноз клика, метрика ROC-AUC > 0.8.
Сохраняет модель и метаданные (список признаков, AUC) в ml/models/. Запуск см. в ml/README.md.
"""
import argparse
import json
import os
from pathlib import Path

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


# Признаки без clicks_7d (целевая метка = clicks_7d > 0, иначе утечка)
FEATURE_COLS = [
    "impressions_7d",
    "actions_7d",
    "recency_days",
    "device_type",
    "os",
]
CAT_COLS = ["device_type", "os", "segment", "tariff"]
TARGET_COL = "target_click"  # binary: был ли хотя бы один клик за 7d (clicks_7d > 0)


def load_features(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if p.suffix.lower() in (".csv", ".csv.gz"):
        return pd.read_csv(path)
    raise ValueError(f"Unsupported format: {p.suffix}")


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "target_click" not in df.columns and "clicks_7d" in df.columns:
        df[TARGET_COL] = (df["clicks_7d"] > 0).astype(int)
    for c in CAT_COLS:
        if c in df.columns:
            df[c] = df[c].fillna("__null__").astype("category").cat.codes
    return df


def main():
    parser = argparse.ArgumentParser(description="Train XGBoost CTR model")
    parser.add_argument("--features-path", type=str, default="ml/data/user_features.parquet")
    parser.add_argument("--model-path", type=str, default="ml/models/xgb_ctr.json")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = load_features(args.features_path)
    df = prepare_df(df)

    use_cols = [c for c in FEATURE_COLS + [c for c in CAT_COLS if c in df.columns] if c in df.columns]
    if TARGET_COL not in df.columns:
        raise ValueError("Need target_click or clicks_7d to build target")
    X = df[use_cols].fillna(0)
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=args.seed,
        eval_metric="auc",
        use_label_encoder=False,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=20,
    )

    pred = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, pred)
    print(f"Test ROC-AUC: {auc:.4f}")

    Path(args.model_path).parent.mkdir(parents=True, exist_ok=True)
    model.save_model(args.model_path)
    meta = {"feature_columns": use_cols, "roc_auc": auc}
    meta_path = args.model_path.replace(".json", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Model saved: {args.model_path}, meta: {meta_path}")


if __name__ == "__main__":
    main()
