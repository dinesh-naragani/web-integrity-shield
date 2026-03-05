#!/usr/bin/env python3
"""Prepare datasets with clear separation:
1) PhiUSIIL multi-column dataset (for Level-1 model training)
2) URL-only datasets kept separate for auxiliary/secondary use
"""

import os
import pandas as pd

BASE_DIR = os.path.join("..", "datasets")
OUTPUT_DIR = "prepared_datasets"

PHIUSIIL_FILE = "PhiUSIIL_Phishing_URL_Dataset.csv"
URL_ONLY_A_FILE = "Phishing URLs.csv"
URL_ONLY_B_FILE = "URL dataset.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("PREPARING SEPARATE DATASETS")
print("=" * 80)

# 1) PhiUSIIL (multi-column) — keep as-is for tabular Level-1 training
phiusiil_path = os.path.join(BASE_DIR, PHIUSIIL_FILE)
phiusiil_df = pd.read_csv(phiusiil_path)
phiusiil_out = os.path.join(OUTPUT_DIR, "phiusiil_multicolumn_training.csv")
phiusiil_df.to_csv(phiusiil_out, index=False)

print(f"\nPhiUSIIL saved: {phiusiil_out}")
print(f"Rows: {len(phiusiil_df):,} | Cols: {len(phiusiil_df.columns)}")

# 2) URL-only A (normalize to url,label)
url_a_path = os.path.join(BASE_DIR, URL_ONLY_A_FILE)
url_a_df = pd.read_csv(url_a_path)
url_a_norm = pd.DataFrame(
    {
        "url": url_a_df["url"].astype(str),
        "label": (url_a_df["Type"].str.lower() == "phishing").astype(int),
    }
)
url_a_out = os.path.join(OUTPUT_DIR, "url_only_dataset_a.csv")
url_a_norm.to_csv(url_a_out, index=False)

print(f"\nURL-only A saved: {url_a_out}")
print(f"Rows: {len(url_a_norm):,} | Phishing: {(url_a_norm['label'] == 1).sum():,} | Legitimate: {(url_a_norm['label'] == 0).sum():,}")

# 3) URL-only B (normalize to url,label)
url_b_path = os.path.join(BASE_DIR, URL_ONLY_B_FILE)
url_b_df = pd.read_csv(url_b_path)
url_b_norm = pd.DataFrame(
    {
        "url": url_b_df["url"].astype(str),
        "label": (url_b_df["type"].str.lower() == "phishing").astype(int),
    }
)
url_b_out = os.path.join(OUTPUT_DIR, "url_only_dataset_b.csv")
url_b_norm.to_csv(url_b_out, index=False)

print(f"\nURL-only B saved: {url_b_out}")
print(f"Rows: {len(url_b_norm):,} | Phishing: {(url_b_norm['label'] == 1).sum():,} | Legitimate: {(url_b_norm['label'] == 0).sum():,}")

# Optional combined URL-only file (still separate from PhiUSIIL)
url_only_combined = pd.concat([url_a_norm, url_b_norm], ignore_index=True)
url_only_combined = url_only_combined.drop_duplicates(subset=["url"], keep="first")
url_only_combined_out = os.path.join(OUTPUT_DIR, "url_only_combined_secondary.csv")
url_only_combined.to_csv(url_only_combined_out, index=False)

print(f"\nURL-only combined saved: {url_only_combined_out}")
print(
    f"Rows: {len(url_only_combined):,} | "
    f"Phishing: {(url_only_combined['label'] == 1).sum():,} | "
    f"Legitimate: {(url_only_combined['label'] == 0).sum():,}"
)

print("\nDone. Strategy applied:")
print("- Level-1 training source: PhiUSIIL multi-column dataset")
print("- Other two datasets: separate URL-only files")
