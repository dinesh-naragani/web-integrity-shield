#!/usr/bin/env python3
"""
Analyze and merge all phishing URL datasets with proper labeling
"""

import pandas as pd
import os

print("=" * 80)
print("📊 DATASET ANALYSIS")
print("=" * 80)

datasets_dir = "../datasets"

# Dataset 1: Phishing URLs.csv
print("\n1️⃣ Phishing URLs.csv")
df1 = pd.read_csv(os.path.join(datasets_dir, "Phishing URLs.csv"))
print(f"   Rows: {len(df1):,}")
print(f"   Columns: {list(df1.columns)}")
print(f"   Type values: {df1['Type'].unique()}")
print(f"   Phishing: {len(df1[df1['Type'].str.lower() == 'phishing']):,}")
print(f"   Legitimate: {len(df1[df1['Type'].str.lower() == 'legitimate']):,}")

# Dataset 2: PhiUSIIL_Phishing_URL_Dataset.csv
print("\n2️⃣ PhiUSIIL_Phishing_URL_Dataset.csv")
df2 = pd.read_csv(os.path.join(datasets_dir, "PhiUSIIL_Phishing_URL_Dataset.csv"))
print(f"   Rows: {len(df2):,}")
print(f"   Label (1=phishing, 0=legitimate)")
print(f"   Phishing (label=1): {len(df2[df2['label'] == 1]):,}")
print(f"   Legitimate (label=0): {len(df2[df2['label'] == 0]):,}")

# Dataset 3: URL dataset.csv
print("\n3️⃣ URL dataset.csv")
df3 = pd.read_csv(os.path.join(datasets_dir, "URL dataset.csv"))
print(f"   Rows: {len(df3):,}")
print(f"   Type values: {df3['type'].unique()}")
print(f"   Phishing: {len(df3[df3['type'].str.lower() == 'phishing']):,}")
print(f"   Legitimate: {len(df3[df3['type'].str.lower() == 'legitimate']):,}")

# Merge datasets
print("\n" + "=" * 80)
print("🔄 MERGING DATASETS")
print("=" * 80)

all_data = []

# Dataset 1: Normalize to (url, label) format
print("\n✓ Processing Phishing URLs.csv...")
for _, row in df1.iterrows():
    url = row['url']
    label = 1 if row['Type'].lower() == 'phishing' else 0
    all_data.append({'url': url, 'label': label})
print(f"  Added {len(df1):,} URLs")

# Dataset 2: Already has URL and label columns
print("\n✓ Processing PhiUSIIL_Phishing_URL_Dataset.csv...")
for _, row in df2.iterrows():
    url = row['URL']
    label = row['label']  # 1=phishing, 0=legitimate
    all_data.append({'url': url, 'label': label})
print(f"  Added {len(df2):,} URLs")

# Dataset 3: Normalize to (url, label) format
print("\n✓ Processing URL dataset.csv...")
for _, row in df3.iterrows():
    url = row['url']
    label = 1 if row['type'].lower() == 'phishing' else 0
    all_data.append({'url': url, 'label': label})
print(f"  Added {len(df3):,} URLs")

# Count before deduplication
total_combined = len(all_data)
print(f"\n📈 Total combined: {total_combined:,} URLs")
print(f"   Phishing (label=1): {sum(1 for d in all_data if d['label'] == 1):,}")
print(f"   Legitimate (label=0): {sum(1 for d in all_data if d['label'] == 0):,}")

# Deduplicate - keep first occurrence
print("\n🔍 Deduplicating...")
seen_urls = set()
unique_data = []

for item in all_data:
    url = item['url']
    if url not in seen_urls:
        seen_urls.add(url)
        unique_data.append(item)

print(f"   Duplicates removed: {total_combined - len(unique_data):,}")
print(f"   Unique URLs: {len(unique_data):,}")

# Final statistics
phishing_count = sum(1 for d in unique_data if d['label'] == 1)
legitimate_count = sum(1 for d in unique_data if d['label'] == 0)

print(f"\n✅ Final merged dataset:")
print(f"   Total URLs: {len(unique_data):,}")
print(f"   Phishing: {phishing_count:,} ({100*phishing_count/len(unique_data):.1f}%)")
print(f"   Legitimate: {legitimate_count:,} ({100*legitimate_count/len(unique_data):.1f}%)")
print(f"   Class balance: {phishing_count/legitimate_count:.2f}:1")

# Save merged dataset
output_file = "merged_dataset.csv"
df_merged = pd.DataFrame(unique_data)
df_merged.to_csv(output_file, index=False)
print(f"\n💾 Saved to {output_file}")
