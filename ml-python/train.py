#!/usr/bin/env python3
"""
Level-1 training using PhiUSIIL multi-column dataset only.

Why:
- PhiUSIIL has rich engineered columns (56 total, 51 numeric features)
- Other datasets are URL-only and are intentionally kept separate
"""

import json
import os
import pickle
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
import xgboost as xgb
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


DATASET_PATH = os.path.join("..", "datasets", "PhiUSIIL_Phishing_URL_Dataset.csv")
TARGET_COLUMN = "label"
TEXT_COLUMNS = ["FILENAME", "URL", "Domain", "TLD", "Title"]
ARTIFACT_PREFIX = "phiusiil"


def evaluate_model(y_true, y_pred, y_proba, train_time):
    return {
        "f1": float(f1_score(y_true, y_pred)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "time": float(train_time),
        "cm": confusion_matrix(y_true, y_pred).tolist(),
    }


print("=" * 80)
print("LEVEL-1 TRAINING (PHIUSIIL MULTI-COLUMN FEATURES)")
print("=" * 80)

if not os.path.exists(DATASET_PATH):
    print(f"Dataset not found: {DATASET_PATH}")
    raise SystemExit(1)

print("\nGPU Status:")
print(f"   CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")
    print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

print(f"\nLoading dataset: {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)

required_columns = set(TEXT_COLUMNS + [TARGET_COLUMN])
missing_required = [col for col in required_columns if col not in df.columns]
if missing_required:
    print(f"Missing required columns: {missing_required}")
    raise SystemExit(1)

feature_candidates = [col for col in df.columns if col not in set(TEXT_COLUMNS + [TARGET_COLUMN])]
numeric_features = df[feature_candidates].select_dtypes(include=[np.number]).columns.tolist()
non_numeric_excluded = [col for col in feature_candidates if col not in numeric_features]

X = df[numeric_features].astype(np.float32)
y = df[TARGET_COLUMN].astype(np.int32)

print(f"Rows: {len(df):,}")
print(f"Total columns: {len(df.columns)}")
print(f"Numeric training features: {len(numeric_features)}")
print(f"Excluded text columns: {TEXT_COLUMNS}")
if non_numeric_excluded:
    print(f"Excluded non-numeric columns: {non_numeric_excluded}")

print(f"Phishing (1): {(y == 1).sum():,} ({100 * (y == 1).mean():.1f}%)")
print(f"Legitimate (0): {(y == 0).sum():,} ({100 * (y == 0).mean():.1f}%)")

print("\nSplitting data (70/15/15)...")
split_start = time.time()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.176, random_state=42, stratify=y_train
)

split_time = time.time() - split_start
print(f"Train: {len(X_train):,}")
print(f"Val  : {len(X_val):,}")
print(f"Test : {len(X_test):,}")

models = {}
results = {}

print("\n" + "=" * 80)
print("Training XGBoost")
print("=" * 80)

xgb_start = time.time()
xgb_model = xgb.XGBClassifier(
    n_estimators=400,
    max_depth=9,
    learning_rate=0.08,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="binary:logistic",
    eval_metric="auc",
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
    device="cuda" if torch.cuda.is_available() else "cpu",
)

xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
xgb_time = time.time() - xgb_start

y_pred_xgb = xgb_model.predict(X_test)
y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
results["xgboost"] = evaluate_model(y_test, y_pred_xgb, y_proba_xgb, xgb_time)
models["xgboost"] = xgb_model

print(f"XGBoost F1: {results['xgboost']['f1']:.4f}")
print(f"Accuracy: {results['xgboost']['accuracy']:.4f}")
print(f"ROC-AUC : {results['xgboost']['roc_auc']:.4f}")
print(f"Time    : {xgb_time:.2f}s")

print("\n" + "=" * 80)
print("Training LightGBM")
print("=" * 80)

lgb_start = time.time()
lgb_model = lgb.LGBMClassifier(
    n_estimators=400,
    max_depth=9,
    learning_rate=0.08,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1,
    verbose=-1,
)

lgb_model.fit(X_train, y_train)
lgb_time = time.time() - lgb_start

y_pred_lgb = lgb_model.predict(X_test)
y_proba_lgb = lgb_model.predict_proba(X_test)[:, 1]
results["lightgbm"] = evaluate_model(y_test, y_pred_lgb, y_proba_lgb, lgb_time)
models["lightgbm"] = lgb_model

print(f"LightGBM F1: {results['lightgbm']['f1']:.4f}")
print(f"Accuracy : {results['lightgbm']['accuracy']:.4f}")
print(f"ROC-AUC  : {results['lightgbm']['roc_auc']:.4f}")
print(f"Time     : {lgb_time:.2f}s")

print("\n" + "=" * 80)
print("Training Ensemble (soft voting)")
print("=" * 80)

ensemble_model = VotingClassifier(
    estimators=[("xgb", xgb_model), ("lgb", lgb_model)],
    voting="soft",
    weights=[1.05, 1.0],
)
ensemble_model.fit(X_train, y_train)

y_pred_ens = ensemble_model.predict(X_test)
y_proba_ens = ensemble_model.predict_proba(X_test)[:, 1]
results["ensemble"] = evaluate_model(y_test, y_pred_ens, y_proba_ens, xgb_time + lgb_time)

print(f"Ensemble F1: {results['ensemble']['f1']:.4f}")
print(f"Accuracy  : {results['ensemble']['accuracy']:.4f}")
print(f"ROC-AUC   : {results['ensemble']['roc_auc']:.4f}")

best_model_name = max(results, key=lambda model_name: results[model_name]["f1"])

print("\n" + "=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
for name, metrics in results.items():
    print(
        f"{name:10s} | F1: {metrics['f1']:.4f} | Acc: {metrics['accuracy']:.4f} | "
        f"AUC: {metrics['roc_auc']:.4f}"
    )

print(f"\nBEST MODEL: {best_model_name.upper()}")

print("\nSaving artifacts...")
os.makedirs("models", exist_ok=True)

trained_models_path = f"models/{ARTIFACT_PREFIX}_trained_models.pkl"
results_path = f"models/{ARTIFACT_PREFIX}_training_results.json"
config_path = f"models/{ARTIFACT_PREFIX}_best_model_config.json"
feature_contract_path = f"models/{ARTIFACT_PREFIX}_feature_contract.json"

with open(trained_models_path, "wb") as handle:
    pickle.dump(
        {
            "models": models,
            "voting": ensemble_model,
            "best_model": best_model_name,
            "results": results,
            "feature_columns": numeric_features,
            "dataset_source": "PhiUSIIL_Phishing_URL_Dataset.csv",
            "excluded_columns": TEXT_COLUMNS,
            "label_column": TARGET_COLUMN,
        },
        handle,
    )
print(f"Saved: {trained_models_path}")

with open(results_path, "w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=2)
print(f"Saved: {results_path}")

with open(config_path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "best_model": best_model_name,
            "metrics": results[best_model_name],
            "dataset": {
                "source": "PhiUSIIL_Phishing_URL_Dataset.csv",
                "total_rows": len(df),
                "phishing": int((y == 1).sum()),
                "legitimate": int((y == 0).sum()),
            },
            "features": {
                "count": len(numeric_features),
                "names": numeric_features,
                "excluded_text_columns": TEXT_COLUMNS,
            },
            "note": "Other two datasets are intentionally kept separate because they are URL-only.",
            "timing_seconds": {
                "split": split_time,
                "xgboost": xgb_time,
                "lightgbm": lgb_time,
                "total": split_time + xgb_time + lgb_time,
            },
        },
        handle,
        indent=2,
    )
print(f"Saved: {config_path}")

url_derived_features = {
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "URLSimilarityIndex",
    "CharContinuationRate",
    "URLCharProb",
}

with open(feature_contract_path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "total_features": len(numeric_features),
            "feature_columns": numeric_features,
            "runtime_extraction_plan": {
                "url_derived_features": [f for f in numeric_features if f in url_derived_features],
                "page_content_or_lookup_features": [f for f in numeric_features if f not in url_derived_features],
            },
            "next_step": "Implement Level-1 runtime extractor for all feature_columns from visited site context.",
        },
        handle,
        indent=2,
    )
print(f"Saved: {feature_contract_path}")

print("\nTraining complete (PhiUSIIL-only Level-1 model)")
