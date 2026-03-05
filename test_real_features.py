import onnxruntime as ort
import numpy as np
from pathlib import Path
import sys

# Try to load feature extractor
try:
    sys.path.insert(0, 'ml-python')
    from comprehensive_feature_extractor import extract_comprehensive_features
    HAS_EXTRACTOR = True
except:
    HAS_EXTRACTOR = False
    print("Warning: Feature extractor not available, using dummy features")

sess = ort.InferenceSession('ml-python/models/level1_xgboost_22features.onnx')
input_name = sess.get_inputs()[0].name

test_urls = {
    'https://www.chatgpt.com': 'LEGITIMATE',
    'https://paypa1.com': 'PHISHING',
}

print("ONNX Model Output Analysis")
print("=" * 70)

if HAS_EXTRACTOR:
    for url, expected in test_urls.items():
        print(f"\nURL: {url}")
        print(f"Expected: {expected}")
        
        result = extract_comprehensive_features(url)
        
        # Handle both tuple and array returns
        if isinstance(result, tuple):
            features = result[0]
        else:
            features = result
            
        features = np.array(features, dtype=np.float32).flatten()
        
        if features.ndim == 1:
            features_batch = features.reshape(1, -1)
        else:
            features_batch = features
            
        result = sess.run(None, {input_name: features_batch})
        class_label = result[0][0]
        probs = result[1][0]
        
        print(f"Extracted Features: {features[:5]}... (shape={features.shape})")
        print(f"ONNX Classification: {class_label}")
        print(f"Probabilities: [{probs[0]:.8f}, {probs[1]:.8f}]")
        print(f"  -> Class 0 (Expected LEGITIMATE): {probs[0]:.8f}")
        print(f"  -> Class 1 (Expected PHISHING):   {probs[1]:.8f}")
else:
    print("Note: Could not import feature extractor")
