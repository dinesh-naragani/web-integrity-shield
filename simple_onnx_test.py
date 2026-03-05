import onnxruntime as ort
import numpy as np

sess = ort.InferenceSession('ml-python/models/level1_xgboost_22features.onnx')

# Create dummy legitimate-looking features (ChatGPT-like)
legit_features = np.array([[
    18, 8, 3, 0, 2, 1, 15, 0, 0, 0, 0, 0,  # Basic features
    0.833, 0, 0, 1, 4.2, 0, 1, 0, 1, 1  # Ratios and binary
]], dtype=np.float32)

# Create dummy phishing-looking features (PayPal spoof)
phish_features = np.array([[
    22, 14, 3, 0, 1, 0, 18, 1, 1, 1, 1, 2,  # Some suspicious patterns
    0.8, 0.05, 0.1, 2, 3.8, 1, 2, 0, 1, 0  # Domain might be suspicious
]], dtype=np.float32)

input_name = sess.get_inputs()[0].name

print("Testing ONNX model outputs:")
print("=" * 60)

for features, label in [(legit_features, "LEGITIMATE"), (phish_features, "PHISHING")]:
    result = sess.run(None, {input_name: features})
    class_label = result[0][0]
    probs = result[1][0]
    
    print(f"\nTest: {label}")
    print(f"  Classification: {class_label}")
    print(f"  Probabilities: [{probs[0]:.8f}, {probs[1]:.8f}]")
    print(f"  Prob[0] (class 0): {probs[0]:.8f}")
    print(f"  Prob[1] (class 1): {probs[1]:.8f}")
    print(f"  -> Using [1]: Risk = {probs[1]:.8f}")
