
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
