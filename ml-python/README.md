# ML Pipeline - Level-1 Phishing Detection

This folder contains the Python-based ML training and export pipeline for the Level-1 phishing detection model.

## Overview

The ML pipeline:
1. **Extracts features** from URLs (deterministically)
2. **Trains a Logistic Regression model** on phishing/legitimate URL dataset
3. **Exports to ONNX** format for Java backend integration
4. **Validates inference** to ensure Python ↔ ONNX consistency

## Architecture

```
feature_extractor.py  ← Deterministic feature extraction (7 features)
    ↓
train.py  ← Trains Logistic Regression model
    ↓
export_onnx.py  ← Converts to ONNX format
    ↓
models/url_model.onnx  ← Ready for Java backend
```

## Features (Level-1)

The model extracts 7 deterministic features from each URL:

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 1 | `url_length` | int | Total length of the URL |
| 2 | `dot_count` | int | Number of dots in URL |
| 3 | `hyphen_count` | int | Number of hyphens in URL |
| 4 | `special_char_count` | int | Special characters: @, #, $, %, &, *, etc. |
| 5 | `has_https` | binary | 1 if HTTPS, 0 otherwise |
| 6 | `has_ip` | binary | 1 if IP address detected, 0 otherwise |
| 7 | `suspicious_keyword_count` | int | Matches against phishing keyword list |

**Critical:** Feature order is fixed and must match Java implementation.

## Suspicious Keywords

The model checks for these common phishing keywords:
- Credential actions: `login`, `signin`, `verify`, `confirm`
- Account terms: `account`, `secure`, `banking`
- Brand names: `paypal`, `amazon`, `apple`, `microsoft`
- URL shorteners: `bit.ly`, `tinyurl`
- Urgency: `urgent`, `alert`, `suspend`

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import sklearn, pandas, numpy, skl2onnx, onnx, onnxruntime; print('✓ All dependencies installed')"
```

## Usage

### Step 1: Train Model

```bash
python train.py
```

**What it does:**
- Loads/creates dataset from sample URLs
- Splits into 70% train, 15% val, 15% test
- Trains Logistic Regression model
- Evaluates metrics (accuracy, precision, recall, F1)
- Saves model to `url_model.pkl`
- Saves metrics to `model_metrics.json`

**Output:**
```
Dataset size: 20 URLs
  Phishing: 10
  Legitimate: 10
Data split:
  Training: 14 URLs
  Validation: 3 URLs
  Test: 3 URLs
============================================================
Model Evaluation Results
============================================================

VALIDATION SET:
  Accuracy:  0.6667
  Precision: 0.5000
  Recall:    1.0000
  F1-Score:  0.6667

TEST SET:
  Accuracy:  0.6667
  Precision: 0.5000
  Recall:    1.0000
  F1-Score:  0.6667
```

### Step 2: Export to ONNX

```bash
python export_onnx.py
```

**What it does:**
- Loads trained model from `url_model.pkl`
- Validates feature extraction determinism
- Converts to ONNX format
- Tests inference consistency (Python vs ONNX)
- Saves to `models/url_model.onnx`

**Output:**
```
✓ ONNX model is valid
✓ All ONNX predictions match sklearn predictions!
✓ EXPORT SUCCESSFUL

ONNX model ready for Java backend integration:
  Location: models/url_model.onnx
  Next step: Copy models/url_model.onnx to backend-java/models/
```

### Step 3: Test Feature Extraction

```python
from feature_extractor import extract_features, get_feature_names

url = "https://www.google.com"
features, feature_dict = extract_features(url)

print(f"Features: {features}")
print(f"Details: {feature_dict}")
```

## Implementation Details

### Feature Extraction (Deterministic)

The `feature_extractor.py` ensures:
- **Deterministic**: Same URL always produces same features
- **Ordered**: Features in fixed order for model consistency
- **Validated**: Ranges checked (binary features are 0/1)

### Model Training

The `train.py` script:
1. Uses Logistic Regression (scikit-learn)
2. Handles class imbalance with `class_weight='balanced'`
3. Evaluates on train/val/test splits
4. Records confusion matrix and metrics

### ONNX Export

The `export_onnx.py` script:
1. Converts sklearn → ONNX using `skl2onnx`
2. Validates ONNX structure with `onnx.checker`
3. Tests inference consistency
4. Saves to `models/url_model.onnx`

## Performance Targets

| Metric | Target |
|--------|--------|
| Accuracy | > 85% |
| Precision | > 80% |
| Recall | > 80% |
| F1-Score | > 80% |

## Java Integration

After export, copy the ONNX model to the Java backend:

```bash
cp models/url_model.onnx ../backend-java/models/url_model.onnx
```

Java backend will:
1. Load model at application startup
2. Extract features using Java implementation (matching Python order)
3. Run inference per user request
4. Return probability score (0–1)

## Common Issues

### Issue: Features don't match between Python and Java

**Solution:** Ensure `feature_extractor.py` and Java implementation use same feature order.

### Issue: ONNX inference differs from sklearn

**Solution:** This indicates a conversion issue. Check:
- Input tensor shape: `[1, 7]` (batch of 1, 7 features)
- Data type: `float32` for ONNX
- Feature scaling: No scaling applied (raw features)

### Issue: Model predicts all negatives or positives

**Solution:** Check dataset balance and use `class_weight='balanced'` in training.

## Dataset Expansion

To improve model performance, expand the dataset:

### Phishing URLs
- PhishTank API: https://phishtank.com/api_info.php
- OpenPhish: https://openphish.com/

### Legitimate URLs
- Alexa top 1000 domains
- GitHub popular repositories
- Wikipedia domains

**Format:** CSV with columns `[url, label]` where `label` is 0 (legit) or 1 (phishing)

## Next Steps

1. ✓ Feature extraction implemented
2. ✓ Model training implemented
3. ✓ ONNX export implemented
4. → Run `train.py` to train model
5. → Run `export_onnx.py` to export ONNX
6. → Move to Phase 2: Java Backend
