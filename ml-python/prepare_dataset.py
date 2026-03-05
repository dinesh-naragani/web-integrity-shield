#!/usr/bin/env python3
"""Merge all phishing URL datasets from ../datasets folder"""

import pandas as pd
import os

print("📁 Merging Datasets...")

datasets_dir = "../datasets"
output_file = "merged_dataset.csv"

files = [
    "Phishing URLs.csv",
    "PhiUSIIL_Phishing_URL_Dataset.csv",
    "URL dataset.csv"
]

all_urls = []
all_labels = []

for filename in files:
    filepath = os.path.join(datasets_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"  ⚠ {filename} not found")
        continue
    
    try:
        df = pd.read_csv(filepath)
        print(f"  ✓ Loaded {filename}: {len(df):,} rows")
        
        # Detect URL and label columns (flexible column naming)
        url_col = None
        label_col = None
        
        for col in df.columns:
            if 'url' in col.lower():
                url_col = col
            elif 'label' in col.lower() or 'class' in col.lower():
                label_col = col
        
        if url_col is None:
            print(f"    ⚠ No URL column found in {filename}")
            continue
        
        urls = df[url_col].dropna().unique()
        all_urls.extend(urls.tolist())
        
        # Handle labels
        if label_col and label_col in df.columns:
            for url in urls:
                mask = df[url_col] == url
                if mask.any():
                    label = df[mask][label_col].iloc[0]
                    # Normalize labels (1 = phishing, 0 = legitimate)
                    if str(label).lower() in ['phishing', '1', 'malicious', 'bad']:
                        all_labels.append(1)
                    else:
                        all_labels.append(0)
        else:
            # Assume all rows in this file are phishing
            all_labels.extend([1] * len(urls))
    
    except Exception as e:
        print(f"  ❌ Error reading {filename}: {e}")

# Remove duplicates while preserving labels
unique_data = {}
for url, label in zip(all_urls, all_labels):
    if url not in unique_data:
        unique_data[url] = label

print(f"\n✓ Merged {len(unique_data):,} unique URLs")
print(f"  Phishing: {sum(1 for l in unique_data.values() if l == 1):,}")
print(f"  Legitimate: {sum(1 for l in unique_data.values() if l == 0):,}")

# Save merged dataset
df_merged = pd.DataFrame({
    'url': list(unique_data.keys()),
    'label': list(unique_data.values())
})

df_merged.to_csv(output_file, index=False)
print(f"\n✓ Saved {output_file}")
