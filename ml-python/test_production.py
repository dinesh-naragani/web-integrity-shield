#!/usr/bin/env python3
"""Test the deployed production model"""

import pickle
import json
import numpy as np
from feature_extractor import extract_features

print("=" * 80)
print("🧪 PRODUCTION MODEL INFERENCE TEST")
print("=" * 80)

# Load production model
print("\n📦 Loading production model...")
with open('models/production_model.pkl', 'rb') as f:
    production_data = pickle.load(f)
    model = production_data['model']
    scaler = production_data['scaler']
    feature_names = production_data['feature_names']

print(f"✓ Model Type: {production_data['model_type'].upper()}")
print(f"✓ Features: {len(feature_names)} ({', '.join(feature_names[:3])}...)")

# Load metadata for risk levels
with open('models/production_metadata.json', 'r') as f:
    metadata = json.load(f)
    risk_threshold = metadata['model_config']['threshold']
    risk_levels = metadata['model_config']['risk_levels']

print(f"✓ Risk Threshold: {risk_threshold}")
print(f"\n📊 Risk Levels:")
for level, range_vals in risk_levels.items():
    print(f"   {level.capitalize()}: {range_vals[0]:.1f} - {range_vals[1]:.1f}")

# Test URLs with ground truth
test_cases = [
    # Format: (url, expected_category, description)
    ('https://www.google.com', 'legitimate', 'Major Tech - Google'),
    ('https://www.amazon.com', 'legitimate', 'Major E-commerce - Amazon'),
    ('https://www.facebook.com', 'legitimate', 'Major Social - Facebook'),
    ('https://www.apple.com', 'legitimate', 'Major Tech - Apple'),
    ('https://www.microsoft.com', 'legitimate', 'Major Tech - Microsoft'),
    ('https://paypal-verify-login.com', 'phishing', 'Phishing - PayPal spoof'),
    ('https://amazon-account-verify.com', 'phishing', 'Phishing - Amazon spoof'),
    ('https://apple-icloud-verify.com', 'phishing', 'Phishing - Apple spoof'),
    ('https://login-secure-facebook.xyz', 'phishing', 'Phishing - Generic domain'),
    ('http://192.168.1.1:8080/admin', 'mixed', 'IP address URL'),
    ('https://example-phishing-site????.com', 'phishing', 'Typo-squatting'),
    ('https://www.github.com', 'legitimate', 'Developer Site'),
    ('https://www.stackoverflow.com', 'legitimate', 'Developer Site'),
]

print(f"\n🧪 Testing {len(test_cases)} URLs...")
print("-" * 100)
print(f"{'URL':<45} | {'Risk':<6} | {'Category':<12} | {'Result':<20}")
print("-" * 100)

correct = 0
total = 0

for url, expected, description in test_cases:
    try:
        # Extract features
        features, feature_vals = extract_features(url)
        X_scaled = scaler.transform([features])
        
        # Get prediction and probability
        pred_prob = model.predict_proba(X_scaled)[0]
        risk_score = pred_prob[1]  # Probability of being phishing
        
        # Determine risk category
        if risk_score < risk_levels['low'][1]:
            risk_category = "Low"
        elif risk_score < risk_levels['medium'][1]:
            risk_category = "Medium"
        else:
            risk_category = "High"
        
        # Determine if phishing or legitimate
        predicted_class = "Phishing" if risk_score > risk_threshold else "Legitimate"
        
        # Check if prediction matches expected (for non-mixed cases)
        if expected != 'mixed':
            expected_class = "Phishing" if expected == 'phishing' else "Legitimate"
            is_correct = (predicted_class == expected_class)
            correct += is_correct if is_correct else 0
            total += 1
            result = "✅ CORRECT" if is_correct else "❌ INCORRECT"
        else:
            result = "⚠️  REVIEW"
        
        print(f"{url:<45} | {risk_score:>5.2%} | {risk_category:<12} | {result:<20}")
        
    except Exception as e:
        print(f"{url:<45} | {'ERROR':<6} | {str(e):<40}")

print("-" * 100)

if total > 0:
    accuracy = (correct / total) * 100
    print(f"\n✅ Test Accuracy: {accuracy:.1f}% ({correct}/{total})")
else:
    print(f"\n⚠️  Could not verify accuracy (check URLs)")

# Model metadata summary
print(f"\n📊 Model Metadata Summary:")
print(f"   Training Dataset: {metadata['dataset_info']['total_urls']:,} URLs")
print(f"   Phishing: {metadata['dataset_info']['phishing']:,} ({metadata['dataset_info']['phishing']/metadata['dataset_info']['total_urls']*100:.1f}%)")
print(f"   Legitimate: {metadata['dataset_info']['legitimate']:,} ({metadata['dataset_info']['legitimate']/metadata['dataset_info']['total_urls']*100:.1f}%)")
print(f"\n   F1-Score: {metadata['metrics']['f1']:.4f}")
print(f"   Accuracy: {metadata['metrics']['accuracy']:.4f}")
print(f"   ROC-AUC: {metadata['metrics']['roc_auc']:.4f}")
print(f"   Training Time: {metadata['metrics']['time']:.2f}s")

print(f"\n✨ Model inference test complete!")
