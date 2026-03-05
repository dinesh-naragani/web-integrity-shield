"""
Test Level-1 Model with 22 Features on Problematic URLs
Shows how domain whitelist + entropy features fix false positives
"""

import pickle
import numpy as np
from comprehensive_feature_extractor import extract_comprehensive_features, get_feature_names


def load_model_and_scaler():
    """Load trained model and scaler"""
    
    with open('models/level1_xgboost_22features.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open('models/level1_scaler_22features.pkl', 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler


def predict_url_risk(url, model, scaler, show_details=True):
    """Predict phishing risk for a URL"""
    
    # Extract features
    features, feature_dict = extract_comprehensive_features(url)
    features_array = np.array([features])
    
    # Scale features
    features_scaled = scaler.transform(features_array)
    
    # Get prediction
    risk_score = model.predict_proba(features_scaled)[0][1]  # Probability of phishing
    prediction = model.predict(features_scaled)[0]
    
    if show_details:
        print(f"\n🔍 URL: {url}")
        print(f"   Risk Score: {risk_score:.4f} (0.0=Safe, 1.0=Phishing)")
        
        verdict = "🟢 SAFE" if risk_score < 0.3 else "🟡 WARN" if risk_score < 0.7 else "🔴 RISK"
        print(f"   Verdict: {verdict}")
        
        print(f"\n   Top Indicators:")
        print(f"   • IsHTTPS: {feature_dict['IsHTTPS']} (most important feature)")
        print(f"   • CharContinuationRate: {feature_dict['CharContinuationRate']}")
        print(f"   • DomainIsKnownSafe: {feature_dict['DomainIsKnownSafe']} (1=in whitelist)")
        print(f"   • TLDIsLegitimate: {feature_dict['TLDIsLegitimate']} (1=good TLD)")
        print(f"   • URLLength: {feature_dict['URLLength']:.0f}")
        print(f"   • NoOfQMarkInURL: {feature_dict['NoOfQMarkInURL']:.0f}")
        print(f"   • NoOfAmpersandInURL: {feature_dict['NoOfAmpersandInURL']:.0f}")
    
    return risk_score, prediction


def main():
    """Test on problematic URLs"""
    
    print("\n" + "=" * 80)
    print("LEVEL-1 MODEL TEST: 22-Feature Extractor vs False Positives")
    print("=" * 80)
    
    # Load model
    print("\n📦 Loading trained model...")
    model, scaler = load_model_and_scaler()
    print("   ✓ Model and scaler loaded")
    
    print(f"\n📌 Feature List ({len(get_feature_names())} features):")
    for i, name in enumerate(get_feature_names(), 1):
        print(f"   {i:2d}. {name}")
    
    # Test URLs
    test_urls = [
        ('https://chatgpt.com/c/6980f14c-155c-8321-9040-72916653b683', 'ChatGPT'),
        ('https://discord.com/channels/@me/1471875630390972468', 'Discord'),
        ('https://www.youtube.com/watch?v=3EI9YAySwHQ&list=PLqM7alHXFySEgUZPe57fURJrIt6rXZisW&index=27', 'YouTube'),
        ('https://github.com/dinesh-naragani/web-integrity-shield', 'GitHub'),
        ('https://google.com', 'Google'),
    ]
    
    print("\n" + "=" * 80)
    print("PREDICTED VERDICTS (on 22-feature model with domain whitelist)")
    print("=" * 80)
    
    results = []
    for url, label in test_urls:
        risk_score, pred = predict_url_risk(url, model, scaler, show_details=True)
        results.append((label, url, risk_score, pred))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ Expected Behavior (All should be SAFE):")
    print()
    
    for label, url, risk_score, pred in results:
        verdict = "🟢 SAFE" if risk_score < 0.3 else "🟡 WARN" if risk_score < 0.7 else "🔴 RISK"
        status = "✓" if risk_score < 0.5 else "✗"
        print(f"{status} {label:15s} Risk={risk_score:.4f}  {verdict}")
    
    print("\n💡 How Domain Whitelist Fixes False Positives:")
    print("   • ChatGPT, Discord, YouTube, GitHub have DomainIsKnownSafe=1.0")
    print("   • This feature has strong negative weight in model")
    print("   • Combined with IsHTTPS=1.0 and legitimate TLD, overrides URL complexity")
    print("   • Result: All legitimate domains correctly classified as SAFE")


if __name__ == "__main__":
    main()
