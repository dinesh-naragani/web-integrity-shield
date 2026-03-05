"""
Train Level-1 Model WITHOUT Hardening Augmentation
Let's verify if the base dataset alone is sufficient
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from xgboost import XGBClassifier
import pickle
import json
from datetime import datetime
from comprehensive_feature_extractor import extract_comprehensive_features, get_feature_names


def extract_features_from_dataset(dataset_path):
    """Extract 22 features from all URLs in dataset"""
    
    print(f"📥 Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"   Total rows: {len(df)}")
    
    # Identify URL column and label column
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
            
            if (idx + 1) % 10000 == 0:
                print(f"   Processed {idx + 1} URLs...", end='\r')
        except Exception:
            failed_urls += 1
    
    X = np.array(features_list)
    y = np.array(labels)
    
    print(f"\n   ✓ Extracted features from {len(features_list)} URLs")
    print(f"   ✓ Legitimate: {sum(y == 0)}")
    print(f"   ✓ Phishing: {sum(y == 1)}")
    
    return X, y


def train_with_cross_validation(X, y):
    """Train with cross-validation"""
    
    print("\n" + "=" * 70)
    print("🚀 XGBoost Training (WITHOUT AUGMENTATION)")
    print("=" * 70)
    
    cv_splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    feature_names = get_feature_names()
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train XGBoost
    xgb_model = XGBClassifier(
        n_estimators=180,
        max_depth=10,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        gamma=0.1,
        min_child_weight=1,
        reg_lambda=1.0,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss',
        verbosity=0
    )
    
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
    
    # Print results
    print("\n📈 CROSS-VALIDATION RESULTS:\n")
    
    metrics_to_track = ['accuracy', 'f1', 'precision', 'recall', 'roc_auc']
    avg_results = {}
    
    for metric in metrics_to_track:
        train_key = f'train_{metric}'
        test_key = f'test_{metric}'
        
        train_scores = cv_results[train_key]
        test_scores = cv_results[test_key]
        
        avg_train = np.mean(train_scores)
        avg_test = np.mean(test_scores)
        std_test = np.std(test_scores)
        gap = avg_train - avg_test
        
        avg_results[metric] = {
            'train': avg_train,
            'test': avg_test,
            'std': std_test,
            'gap': gap
        }
        
        print(f"  {metric.upper()}:")
        print(f"    Test:  {avg_test:.4f} ± {std_test:.4f}")
        print(f"    Gap:   {gap:.4f}")
        print()
    
    # Train final model
    print("🏆 Training final model on all data...")
    xgb_model.fit(X_scaled, y)
    
    # Get feature importance
    importance = xgb_model.feature_importances_
    feature_importance_dict = {
        name: float(imp) for name, imp in zip(feature_names, importance)
    }
    
    print("\n📊 Top 10 Most Important Features:")
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    for i, (name, imp) in enumerate(sorted_features[:10], 1):
        print(f"   {i:2d}. {name:30s} {imp:7.4f}")
    
    return xgb_model, scaler, avg_results, feature_importance_dict


def test_on_reference_urls(model, scaler):
    """Test model on reference legitimate and phishing URLs"""
    
    print("\n" + "=" * 70)
    print("✅ TESTING ON REFERENCE URLS")
    print("=" * 70)
    
    test_cases = [
        ("https://www.chatgpt.com", "LEGITIMATE"),
        ("https://discord.com", "LEGITIMATE"),
        ("https://www.youtube.com", "LEGITIMATE"),
        ("https://github.com", "LEGITIMATE"),
        ("https://paypa1.com", "PHISHING"),
        ("http://192.168.1.1/login", "PHISHING"),
        ("http://secure-login-paypal-verify.tk/account", "PHISHING"),
    ]
    
    print("\nResults:\n")
    correct_predictions = 0
    
    for url, expected_label in test_cases:
        try:
            features, _ = extract_comprehensive_features(url)
            features_array = np.array([features])
            features_scaled = scaler.transform(features_array)
            
            prediction = model.predict(features_scaled)[0]
            probabilities = model.predict_proba(features_scaled)[0]
            phishing_prob = probabilities[1]
            
            predicted_label = "PHISHING" if prediction == 1 else "LEGITIMATE"
            
            is_correct = (predicted_label == expected_label)
            status = "✓" if is_correct else "✗"
            
            if is_correct:
                correct_predictions += 1
            
            print(f"{status} {url:50s}")
            print(f"   Expected: {expected_label:12s} | Predicted: {predicted_label:12s} | Prob: {phishing_prob:.6f}\n")
        
        except Exception as e:
            print(f"✗ {url}: Error - {e}\n")
    
    print(f"\nAccuracy on reference set: {correct_predictions}/{len(test_cases)} ({100*correct_predictions/len(test_cases):.1f}%)")


def main():
    """Main training pipeline"""
    
    print("\n" + "=" * 70)
    print("RETRAINING WITHOUT HARDENING AUGMENTATION")
    print("=" * 70 + "\n")
    
    dataset_path = '../datasets/PhiUSIIL_Phishing_URL_Dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    # Extract features
    X, y = extract_features_from_dataset(dataset_path)
    
    # Train
    model, scaler, cv_results, feature_importance = train_with_cross_validation(X, y)
    
    # Test on reference URLs
    test_on_reference_urls(model, scaler)
    
    # Save models
    os.makedirs('models', exist_ok=True)
    
    with open('models/level1_xgboost_22features_no_aug.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open('models/level1_scaler_22features_no_aug.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"\n✅ Models saved to models/ directory")
    
    return model, scaler


if __name__ == "__main__":
    main()
