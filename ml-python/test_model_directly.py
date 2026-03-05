"""
Test the trained Python model directly to see if it discriminates properly
"""

import pickle
import numpy as np
from comprehensive_feature_extractor import extract_comprehensive_features

# Load model and scaler
print("Loading model and scaler...")
with open('models/level1_xgboost_22features.pkl', 'rb') as f:
    model = pickle.load(f)

with open('models/level1_scaler_22features.pkl', 'rb') as f:
    scaler = pickle.load(f)

print("✓ Model and scaler loaded\n")

# Test URLs
test_urls = [
    ("https://www.chatgpt.com", "LEGITIMATE"),
    ("https://discord.com", "LEGITIMATE"),
    ("https://www.youtube.com", "LEGITIMATE"),
    ("https://paypa1.com", "PHISHING"),
    ("http://192.168.1.1/login", "PHISHING"),
    ("http://secure-login-paypal-verify.tk/account", "PHISHING"),
]

print("=" * 80)
print("PYTHON MODEL TEST")
print("=" * 80)
print()

for url, expected_label in test_urls:
    print(f"URL: {url}")
    print(f"Expected: {expected_label}")
    
    # Extract features
    try:
        features, _ = extract_comprehensive_features(url)
        features_array = np.array([features])
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        
        # Get prediction
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        print(f"Predicted Class: {prediction} ({'LEGITIMATE' if prediction == 0 else 'PHISHING'})")
        print(f"Probabilities: [Class 0: {probabilities[0]:.6f}, Class 1: {probabilities[1]:.6f}]")
        print(f"Phishing Probability: {probabilities[1]:.6f}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")

print("=" * 80)
