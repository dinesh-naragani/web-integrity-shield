"""
Compare Python model predictions with ONNX model predictions
"""

import pickle
import numpy as np
import onnxruntime as ort
from comprehensive_feature_extractor import extract_comprehensive_features

# Load Python model
print("Loading models...")
with open('models/level1_xgboost_22features.pkl', 'rb') as f:
    python_model = pickle.load(f)

with open('models/level1_scaler_22features.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Load ONNX model
sess = ort.InferenceSession('models/level1_xgboost_22features.onnx')
print("✓ Models loaded\n")

# Test URLs
test_urls = [
    ("https://www.chatgpt.com", "LEGITIMATE"),
    ("https://discord.com", "LEGITIMATE"),
    ("https://www.youtube.com", "LEGITIMATE"),
    ("https://paypa1.com", "PHISHING"),
    ("http://192.168.1.1/login", "PHISHING"),
    ("http://secure-login-paypal-verify.tk/account", "PHISHING"),
]

print("=" * 120)
print("PYTHON vs ONNX MODEL COMPARISON")
print("=" * 120)
print()

for url, expected_label in test_urls:
    print(f"\nURL: {url}")
    print(f"Expected: {expected_label}")
    
    # Extract features
    features, _ = extract_comprehensive_features(url)
    features_array = np.array([features])
    
    # --- PYTHON MODEL ---
    features_scaled = scaler.transform(features_array)
    python_pred = python_model.predict(features_scaled)[0]
    python_probs = python_model.predict_proba(features_scaled)[0]
    
    # --- ONNX MODEL ---
    # First check: does ONNX expect scaled or raw features?
    # Try RAW features first
    try:
        onnx_input = {'float_input': features_array.astype(np.float32)}
        onnx_result = sess.run(None, onnx_input)
        onnx_label_raw = onnx_result[0][0] if len(onnx_result) > 0 else -1
        onnx_probs_raw = onnx_result[1][0] if len(onnx_result) > 1 else None
        print(f"\n  ONNX (RAW features):")
        print(f"    Label: {onnx_label_raw}")
        print(f"    Probs: {onnx_probs_raw}")
    except Exception as e:
        print(f"  ONNX (RAW): Error - {e}")
    
    # Try SCALED features
    try:
        onnx_input = {'float_input': features_scaled.astype(np.float32)}
        onnx_result = sess.run(None, onnx_input)
        onnx_label_scaled = onnx_result[0][0] if len(onnx_result) > 0 else -1
        onnx_probs_scaled = onnx_result[1][0] if len(onnx_result) > 1 else None
        print(f"\n  ONNX (SCALED features):")
        print(f"    Label: {onnx_label_scaled}")
        print(f"    Probs: {onnx_probs_scaled}")
    except Exception as e:
        print(f"  ONNX (SCALED): Error - {e}")
    
    print(f"\n  Python Model:")
    print(f"    Pred:  {python_pred} ({'PHISHING' if python_pred == 1 else 'LEGITIMATE'})")
    print(f"    Probs: Class 0={python_probs[0]:.6f}, Class 1={python_probs[1]:.6f}")
    print(f"    Phishing Prob: {python_probs[1]:.6f}")
