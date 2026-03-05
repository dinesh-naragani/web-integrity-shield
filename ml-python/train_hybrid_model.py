"""
Hybrid Phishing Detection: Rules + ML Model
Uses domain whitelist and feature-based rules combined with XGBoost
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, roc_auc_score
from xgboost import XGBClassifier
import pickle
import json
from datetime import datetime
from comprehensive_feature_extractor import extract_comprehensive_features, get_feature_names


# Domain whitelists to prevent false positives
KNOWN_LEGITIMATE_DOMAINS = {
    'google.com', 'gmail.com', 'youtube.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'github.com', 'stackoverflow.com', 'reddit.com', 'linkedin.com',
    'amazon.com', 'ebay.com', 'paypal.com', 'microsoft.com', 'apple.com',
    'netflix.com', 'discord.com', 'twitch.tv', 'slack.com', 'dropbox.com',
    'notion.so', 'figma.com', 'adobe.com', 'spotify.com', 'wikipedia.org',
    'chatgpt.com', 'openai.com', 'anthropic.com', 'gemini.google.com', 'claude.ai'
}


def check_domain_whitelist(domain):
    """Check if domain is in whitelist"""
    domain_lower = domain.lower()
    
    # Direct match
    if domain_lower in KNOWN_LEGITIMATE_DOMAINS:
        return True
    
    # Subdomain match (e.g., mail.google.com -> google.com)
    parts = domain_lower.split('.')
    if len(parts) > 2:
        main_domain = '.'.join(parts[-2:])
        if main_domain in KNOWN_LEGITIMATE_DOMAINS:
            return True
    
    return False


def extract_features_from_dataset(dataset_path):
    """Extract 22 features from all URLs in dataset"""
    
    print(f"📥 Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"   Total rows: {len(df)}")
    
    url_col = None
    label_col = None
    
    for col in df.columns:
        if col.lower() in ['url', 'urls']:
            url_col = col
        if col.lower() in ['label', 'target', 'classification']:
            label_col = col
    
    if not url_col or not label_col:
        raise ValueError("❌ Could not identify URL or label column!")
    
    print(f"   URL Column: {url_col}")
    print(f"   Label Column: {label_col}")
    
    print("\n🔍 Extracting 22 features from URLs...")
    features_list = []
    labels = []
    failed_urls = 0
    
    for idx, row in df.iterrows():
        try:
            url = str(row[url_col]).strip()
            label = int(row[label_col])
            
            if not url or url == 'nan':
                failed_urls += 1
                continue
            
            features, _ = extract_comprehensive_features(url)
            features_list.append(features)
            labels.append(label)
            
            if (idx + 1) % 50000 == 0:
                print(f"   Processed {idx + 1} URLs...", end='\r')
        except Exception:
            failed_urls += 1
    
    X = np.array(features_list)
    y = np.array(labels)
    
    print(f"\n   ✓ Extracted features from {len(features_list)} URLs")
    print(f"   ✓ Legitimate: {sum(y == 0)} ({100*sum(y == 0)/len(y):.1f}%)")
    print(f"   ✓ Phishing: {sum(y == 1)} ({100*sum(y == 1)/len(y):.1f}%)")
    
    return X, y


def train_hybrid_model(X, y):
    """
    Train model focused on harder-to-detect phishing (non-obvious cases)
    Use aggressive regularization to prevent feature dominance
    """
    
    print("\n" + "=" * 70)
    print("🚀 Hybrid Model Training (Rules + XGBoost)")
    print("=" * 70)
    
    cv_splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    feature_names = get_feature_names()
    
    # Normalize features
    print("\n📊 Preprocessing...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"Dataset: {len(y)} samples")
    print(f"  Legitimate (0): {sum(y == 0)}")
    print(f"  Phishing (1): {sum(y == 1)}")
    
    # Calculate class weights
    n_samples = len(y)
    n_classes = 2
    class_counts = np.bincount(y)
    class_weights = n_samples / (n_classes * class_counts)
    sample_weight = np.array([class_weights[label] for label in y])
    
    print(f"\n⚖️  Class weights: {dict(enumerate(class_weights))}")
    
    print("\n🔧 Training with aggressive regularization...")
    
    # VERY aggressive regularization to prevent feature dominance
    xgb_model = XGBClassifier(
        # Tree structure - deeper to capture interactions
        n_estimators=350,
        max_depth=13,
        min_child_weight=2,
        
        # Learning - moderate rate for stability
        learning_rate=0.08,
        subsample=0.7,
        colsample_bytree=0.6,  # Very low - force feature diversity
        colsample_bylevel=0.6,
        
        # AGGRESSIVE Regularization
        gamma=3.0,
        reg_lambda=5.0,  # Very high L2 regularization
        reg_alpha=2.0,   # High L1 regularization
        
        # GPU settings
        device='cuda',
        tree_method='hist',
        
        # Other
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=42,
        use_label_encoder=False,
        verbosity=0
    )
    
    print("   Training...")
    xgb_model.fit(X_scaled, y, sample_weight=sample_weight)
    
    print("✅ Training complete\n")
    
    # Evaluate
    print("📈 Cross-Validation Results:")
    print("=" * 70)
    
    scoring = {
        'accuracy': 'accuracy',
        'f1': 'f1',
        'precision': 'precision',
        'recall': 'recall',
        'roc_auc': 'roc_auc'
    }
    
    cv_results = cross_validate(
        xgb_model, X_scaled, y,
        cv=cv_splitter,
        scoring=scoring,
        return_train_score=True,
        n_jobs=1
    )
    
    metrics_to_track = ['accuracy', 'f1', 'precision', 'recall', 'roc_auc']
    avg_results = {}
    
    for metric in metrics_to_track:
        test_scores = cv_results[f'test_{metric}']
        avg_test = np.mean(test_scores)
        std_test = np.std(test_scores)
        
        avg_results[metric] = {
            'test': avg_test,
            'std': std_test
        }
        
        print(f"  ✓ {metric.upper():10s} Test: {avg_test:.4f} ± {std_test:.4f}")
    
    # Feature importance
    print("\n📊 Feature Importance (after aggressive regularization):")
    print("=" * 70)
    importance = xgb_model.feature_importances_
    feature_importance_dict = {
        name: float(imp) for name, imp in zip(feature_names, importance)
    }
    
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    for i, (name, imp) in enumerate(sorted_features[:15], 1):
        bar = "█" * int(imp * 100)
        print(f"   {i:2d}. {name:30s} {imp:7.4f} {bar}")
    
    return xgb_model, scaler, avg_results, feature_importance_dict


def test_hybrid_detection(model, scaler):
    """Test hybrid detection (rules + model)"""
    
    print("\n" + "=" * 70)
    print("🧪 Testing Hybrid Detection (Domain Whitelist + ML Model)")
    print("=" * 70 + "\n")
    
    test_cases = [
        # Legitimate - known domains
        ("https://www.chatgpt.com", "LEGITIMATE", "known-domain"),
        ("https://discord.com", "LEGITIMATE", "known-domain"),
        ("https://www.youtube.com", "LEGITIMATE", "known-domain"),
        ("https://github.com", "LEGITIMATE", "known-domain"),
        ("https://www.google.com", "LEGITIMATE", "known-domain"),
        ("https://mail.google.com", "LEGITIMATE", "known-domain"),
        ("https://accounts.google.com/signin", "LEGITIMATE", "known-domain"),
        
        # Legitimate - unknown domain
        ("https://example-startup.com", "LEGITIMATE", "unknown-domain"),
        
        # Phishing
        ("http://paypa1.com/verify-account", "PHISHING", "typosquatting"),
        ("http://45.77.12.99/login?session=abc", "PHISHING", "IP-based"),
        ("http://secure-login-paypal-verify.tk/account", "PHISHING", "suspicious-tld"),
        ("http://apple-id-security-update.ga/login", "PHISHING", "suspicious-tld"),
        ("https://secure-amazon-login-verify.ml/account", "PHISHING", "spoofing"),
    ]
    
    correct_hybrid = 0
    correct_model_only = 0
    
    for url, expected, reason in test_cases:
        try:
            # Extract domain for whitelist check
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            
            # HYBRID: Check whitelist first
            if check_domain_whitelist(domain):
                hybrid_pred = "LEGITIMATE"
            else:
                # Else use model
                features, _ = extract_comprehensive_features(url)
                features_scaled = scaler.transform([features])
                pred_class = model.predict(features_scaled)[0]
                pred_proba = model.predict_proba(features_scaled)[0]
                
                hybrid_pred = "PHISHING" if pred_class == 1 else "LEGITIMATE"
                
            # Model-only prediction
            features, _ = extract_comprehensive_features(url)
            features_scaled = scaler.transform([features])
            model_pred = model.predict(features_scaled)[0]
            predict_proba = model.predict_proba(features_scaled)[0]
            model_only_pred = "PHISHING" if model_pred == 1 else "LEGITIMATE"
            
            hybrid_correct = (hybrid_pred == expected)
            model_correct = (model_only_pred == expected)
            
            if hybrid_correct:
                correct_hybrid += 1
            if model_correct:
                correct_model_only += 1
            
            status_hybrid = "✓" if hybrid_correct else "✗"
            status_model = "✓" if model_correct else "✗"
            
            print(f"{status_hybrid} HYBRID | {status_model} MODEL | {reason:15s} | {url:50s}")
            print(f"   Expected: {expected:12s} | Hybrid: {hybrid_pred:12s} | Model: {model_only_pred:12s} | Prob: {predict_proba[1]:.4f}\n")
        
        except Exception as e:
            print(f"✗ Error: {url}: {str(e)[:60]}\n")
    
    print(f"\n{'='*70}")
    hybrid_acc = 100 * correct_hybrid / len(test_cases)
    model_acc = 100 * correct_model_only / len(test_cases)
    
    print(f"Hybrid Accuracy (Whitelist + Model): {correct_hybrid}/{len(test_cases)} ({hybrid_acc:.1f}%)")
    print(f"Model-Only Accuracy:                 {correct_model_only}/{len(test_cases)} ({model_acc:.1f}%)")
    print(f"Improvement: {hybrid_acc - model_acc:+.1f}%")
    print("=" * 70)


def save_models(model, scaler, avg_results, feature_importance, output_dir='models'):
    """Save trained model and scaler"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(output_dir, 'level1_xgboost_22features.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model saved: {model_path}")
    
    # Save scaler
    scaler_path = os.path.join(output_dir, 'level1_scaler_22features.pkl')
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved: {scaler_path}")
    
    # Save whitelist
    whitelist_path = os.path.join(output_dir, 'domain_whitelist.json')
    with open(whitelist_path, 'w') as f:
        json.dump({'whitelist': sorted(list(KNOWN_LEGITIMATE_DOMAINS))}, f, indent=2)
    print(f"✅ Whitelist saved: {whitelist_path}")
    
    # Save model info
    feature_names = get_feature_names()
    model_info = {
        'model_type': 'hybrid_xgboost',
        'approach': 'domain_whitelist + ml_model',
        'n_features': 22,
        'feature_names': feature_names,
        'feature_importance': feature_importance,
        'whitelist_size': len(KNOWN_LEGITIMATE_DOMAINS),
        'cross_val_results': avg_results,
        'trained_at': datetime.now().isoformat()
    }
    
    info_path = os.path.join(output_dir, 'level1_model_info_22features.json')
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    print(f"✅ Model info saved: {info_path}")


def main():
    """Main training pipeline"""
    
    print("\n" + "=" * 70)
    print("HYBRID PHISHING DETECTION MODEL TRAINING")
    print("Domain Whitelist + GPU-Accelerated XGBoost")
    print("=" * 70 + "\n")
    
    # Load dataset
    dataset_path = '../datasets/PhiUSIIL_Phishing_URL_Dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    # Extract features
    X, y = extract_features_from_dataset(dataset_path)
    
    # Train model
    model, scaler, cv_results, feature_importance = train_hybrid_model(X, y)
    
    # Test hybrid approach
    test_hybrid_detection(model, scaler)
    
    # Save models
    save_models(model, scaler, cv_results, feature_importance)
    
    print("\n" + "=" * 70)
    print("✅ HYBRID MODEL TRAINING COMPLETED")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Export ONNX model: python export_onnx_22features.py")
    print("2. Copy whitelist to Java backend")
    print("3. Update backend to use hybrid detection")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
