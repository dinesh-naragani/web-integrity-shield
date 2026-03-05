import numpy as np
import onnxruntime as ort
from pathlib import Path
import pickle
import json

# Load ONNX model
onnx_path = Path('ml-python/models/level1_xgboost_22features.onnx')
sess = ort.InferenceSession(str(onnx_path))

# Load scaler
with open('ml-python/models/level1_scaler_22features.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Load scaler params
with open('ml-python/models/level1_scaler_params_22features.json') as f:
    scaler_params = json.load(f)

# Create a test feature vector for ChatGPT (22 features)
# These are raw extracted features (not normalized)
raw_features = np.array([[ 
    18,      # URLLength
    8,       # DomainLength
    3,       # TLDLength
    0,       # IsDomainIP
    2,       # NoOfSubDomain
    1,       # IsHTTPS
    15,      # NoOfLettersInURL
    0,       # NoOfDigitsInURL
    0,       # NoOfEqualsInURL
    0,       # NoOfQMarkInURL
    0,       # NoOfAmpersandInURL
    0,       # NoOfOtherSpecialCharsInURL
    0.833,   # LetterRatioInURL
    0,       # DigitRatioInURL
    0,       # SpecialCharRatioInURL
    1,       # CharContinuationRate
    4.2,     # URLCharProb
    0,       # DomainHasHyphen
    1,       # URLHasDblSlash
    0,       # HasObfuscation
    1,       # TLDIsLegitimate
    1        # DomainIsKnownSafe
]], dtype=np.float32)

print("Raw Features shape:", raw_features.shape)
print("Raw Features (first 5):", raw_features[0][:5])

# Test 1: Send raw features directly to ONNX
input_name = sess.get_inputs()[0].name
output_name = sess.get_outputs()[0].name
print(f"\nONNX Input name: {input_name}, Output name: {output_name}")

pred_raw = sess.run([output_name], {input_name: raw_features})[0]
print(f"\nONNX Prediction (RAW features): {pred_raw[0]}")

# Test 2: Send normalized features to ONNX
normalized_features = scaler.transform(raw_features)
print(f"\nNormalized Features (first 5): {normalized_features[0][:5]}")

pred_normalized = sess.run([output_name], {input_name: normalized_features})[0]
print(f"ONNX Prediction (NORMALIZED features): {pred_normalized[0]}")

# Conclusion
print(f"\n=== ANALYSIS ===")
print(f"Raw prediction shape: {pred_raw.shape}, Value: {pred_raw}")
print(f"Normalized prediction shape: {pred_normalized.shape}, Value: {pred_normalized}")

if pred_raw.shape == ():
    raw_val = float(pred_raw)
    norm_val = float(pred_normalized)
else:
    raw_val = float(pred_raw[0][0]) if len(pred_raw.shape) > 1 else float(pred_raw[0])
    norm_val = float(pred_normalized[0][0]) if len(pred_normalized.shape) > 1 else float(pred_normalized[0])

print(f"Raw value: {raw_val:.8f}")
print(f"Normalized value: {norm_val:.8f}")

if abs(raw_val - norm_val) < 0.01:
    print("✓ Model expects NORMALIZED input (small difference)")
else:
    print("✗ Model expects RAW input (large difference)")
