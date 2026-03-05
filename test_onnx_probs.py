import onnxruntime as ort
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, 'ml-python')

from comprehensive_feature_extractor import extract_comprehensive_features

# Initialize ONNX session
sess = ort.InferenceSession('ml-python/models/level1_xgboost_22features.onnx')

# Test URLs
urls = {
    'https://www.chatgpt.com': 0,  # Should be legitimate (class 0)
    'https://paypa1.com': 1,  # Should be phishing (class 1)
    'https://185.25.110.110/paypal': 1  # Should be phishing (class 1)
}

input_name = sess.get_inputs()[0].name

print("Testing ONNX outputs:")
print("-" * 80)

for url, expected_class in urls.items():
    # Extract features
    features = extract_comprehensive_features(url)
    if isinstance(features, tuple):
        features = np.array(features, dtype=np.float32)
    elif not isinstance(features, np.ndarray):
        features = np.array(features, dtype=np.float32)
    
    if features.ndim == 1:
        features_batch = features.reshape(1, -1)
    else:
        features_batch = features
    
    # Run inference
    result = sess.run(None, {input_name: features_batch})
    label = result[0][0]  # Classification label
    probs = result[1][0]  # Probabilities [prob_class_0, prob_class_1]
    
    print(f"\nURL: {url}")
    print(f"  Expected: {'LEGITIMATE (class 0)' if expected_class == 0 else 'PHISHING (class 1)'}")
    print(f"  Label: {label}")
    print(f"  Probabilities: [{probs[0]:.8f}, {probs[1]:.8f}]")
    print(f"  Prob[0] (LEGITIMATE): {probs[0]:.8f}")
    print(f"  Prob[1] (PHISHING):   {probs[1]:.8f}")
    print(f"  Predicted: {'LEGITIMATE' if label == 0 else 'PHISHING'}")
