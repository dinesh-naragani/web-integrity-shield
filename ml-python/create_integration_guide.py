"""
Model Export Summary & Java Integration Guide

This document summarizes the trained model and provides integration paths for the Java backend.
"""

import os
import json
import pickle
from pathlib import Path

def generate_integration_guide():
    """Generate a comprehensive model integration guide"""
    
    guide = """
# Web Integrity Shield - Model Integration Guide

## Current Model State

### ✓ Model Available
- **Location**: `models/url_model.pkl`
- **Format**: Python pickle (scikit-learn LogisticRegression)
- **Size**: ~1-2 KB
- **Type**: Logistic Regression (L2 regularization, balanced classes)

### Feature Configuration
- **Features**: 7 deterministic URL features
- **Order**: Fixed and matching Java implementation
- **Config file**: `feature_config.json`

### Performance Metrics
- **Accuracy**: 89.47%
- **Precision**: 92.31%
- **Recall**: 92.31%
- **F1-Score**: 92.31%

---

## Integration Options for Java Backend

### Option 1: Python Bridge (Recommended for Phase 2)
Use FastAPI to wrap the model and expose it via REST endpoint.

**Advantages:**
- Fastest implementation
- No Java ONNX runtime dependency
- Easy debugging and model updates
- Can add Level-2 Selenium integration in same service

**Steps:**
1. Create FastAPI endpoint: `POST /level-1-check`
2. Receive URL, extract features using Python `feature_extractor.py`
3. Load model from pickle
4. Return risk score

**File**: `ml-python/api_server.py` (create next)

```python
from fastapi import FastAPI
from feature_extractor import extract_features
import pickle

app = FastAPI()
with open('models/url_model.pkl', 'rb') as f:
    model = pickle.load(f)

@app.post("/level-1-check")
async def level1_check(url: str):
    features, _ = extract_features(url)
    risk_score = model.predict_proba([features])[0, 1]
    return {"risk_score": risk_score}
```

### Option 2: ONNX Export (Optional, for later)
Convert to ONNX for native Java integration via ONNX Runtime.

**Status**: Currently has file locking issues due to pip conflicts
**Workaround**: Can be done after Phase 2 in a fresh Python environment

**Command when ready:**
```bash
python -m pip install --user --upgrade onnx skl2onnx onnxruntime --force-reinstall
python convert_to_onnx.py
```

**Result**: `models/url_model.onnx` (for Java ONNX Runtime)

---

## Files Ready for Phase 2

✓ `models/url_model.pkl` - Trained model
✓ `feature_config.json` - Feature metadata
✓ `feature_extractor.py` - Deterministic feature extraction
✓ `model_metrics.json` - Performance metrics

---

## Phase 2 Architecture Decision

### Recommended Path:
```
Extension 
    ↓
Java Backend (Spring Boot)
    ↓
Python FastAPI (Feature extraction + Model inference)
    ↓
Trained Model (pickle)
    ↓
Selenium Service (Level-2, on demand)
```

This approach:
1. Keeps feature extraction deterministic in Python
2. Avoids Java/ONNX complexity in Phase 2
3. Allows easy model updates
4. Can integrate Level-2 Selenium in same Python service

---

## Model Inference Example

### Using Python:
```python
import pickle
from feature_extractor import extract_features

# Load model
with open('models/url_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Prepare input
url = "https://example.com"
features, _ = extract_features(url)
X = np.array([features])

# Predict
risk_score = model.predict_proba(X)[0, 1]
label = "PHISHING" if risk_score >= 0.7 else "LEGITIMATE"
```

### Expected Outputs:
- Risk score: Float (0.0 to 1.0)
- Threshold for Level-2: >= 0.7
- Inference time: < 5ms

---

## ONNX Export (For Future Reference)

If Java integration via ONNX is needed later:

### Java Code Example:
```java
import ai.onnxruntime.*;

// Load ONNX model
OrtEnvironment env = OrtEnvironment.getEnvironment();
OrtSession session = env.createSession("models/url_model.onnx");

// Prepare input [1, 7] float array
float[][] input = {{urlLength, dotCount, hyphenCount, 
                     specialChars, hasHttps, hasIp, keywordCount}};

// Run inference
OrtSession.Result results = session.run(Collections.singletonMap(
    "float_input", env.createTensor(input)));

// Get output probability
float riskScore = ((float[][])results.get(0).getValue())[0][1];
```

---

## Next Steps

1. ✓ Phase 1: ML Model trained and exported
2. → Phase 2: Java Backend + Python FastAPI wrapper
3. → Phase 3: Selenium deep analysis service
4. → Phase 4: Browser extension
5. (Optional) Phase 2B: ONNX conversion for direct Java integration

**Proceed with Phase 2 using Python FastAPI bridge.**
"""
    
    return guide


def create_model_manifest():
    """Create a manifest file documenting the model"""
    
    manifest = {
        "project": "Web Integrity Shield",
        "phase": "Phase 1 - Complete",
        "model": {
            "type": "LogisticRegression",
            "framework": "scikit-learn",
            "file": "models/url_model.pkl",
            "size_kb": 1.5,
            "features": 7,
            "input_shape": [None, 7],
            "output": "probability_score",
            "output_range": [0.0, 1.0]
        },
        "training": {
            "dataset": "PhishTank (56,266 URLs) + 41 legitimate URLs",
            "train_size": 86,
            "validation_size": 18,
            "test_size": 19,
            "train_split": "70-15-15"
        },
        "performance": {
            "test_accuracy": 0.8947,
            "test_precision": 0.9231,
            "test_recall": 0.9231,
            "test_f1": 0.9231,
            "confusion_matrix": {
                "true_negatives": 5,
                "false_positives": 1,
                "false_negatives": 1,
                "true_positives": 12
            }
        },
        "features": {
            "names": [
                "url_length",
                "dot_count",
                "hyphen_count",
                "special_char_count",
                "has_https",
                "has_ip",
                "suspicious_keyword_count"
            ],
            "deterministic": True,
            "feature_order_critical": True
        },
        "integration": {
            "phase_2_path": "Python FastAPI Bridge",
            "onnx_export": "Optional for Phase 2B",
            "threshold": 0.7
        },
        "files": {
            "model": "models/url_model.pkl",
            "config": "feature_config.json",
            "metrics": "model_metrics.json",
            "feature_extractor": "feature_extractor.py"
        }
    }
    
    return manifest


def main():
    print("Generating Model Integration Documentation...\n")
    
    # Create integration guide
    guide_path = "INTEGRATION_GUIDE.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(generate_integration_guide())
    print(f"✓ Created {guide_path}")
    
    # Create manifest
    manifest = create_model_manifest()
    manifest_path = "models/model_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Created {manifest_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("MODEL STATUS SUMMARY")
    print("=" * 70)
    print(f"\nModel: Logistic Regression (scikit-learn)")
    print(f"Status: ✓ TRAINED AND READY")
    print(f"Format: Python pickle (models/url_model.pkl)")
    print(f"Performance: 89.47% accuracy on test set")
    print(f"\nIntegration Path: Python FastAPI Bridge")
    print(f"  - Feature extraction: Python (deterministic)")
    print(f"  - Model inference: Python (pickle)")
    print(f"  - REST endpoint: FastAPI")
    print(f"  - Java communication: HTTP JSON")
    print(f"\nONNX Export: Optional (can be done later in isolated environment)")
    print(f"\n✓ Ready for Phase 2 Backend Development")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    main()
