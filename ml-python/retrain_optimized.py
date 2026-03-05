"""
Retrain Level-1 Model with Optimized Hyperparameters
Focus on better feature balance and discrimination
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_validate, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, roc_curve
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


def train_optimized_model(X, y):
    """
    Train with hyperparameter tuning for better discrimination
    """
    
    print("\n" + "=" * 70)
    print("🚀 XGBoost Hyperparameter Optimization")
    print("=" * 70)
    
    cv_splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    feature_names = get_feature_names()
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"\nDataset: {len(y)} samples")
    print(f"  Legitimate: {sum(y == 0)} ({100*sum(y == 0)/len(y):.1f}%)")
    print(f"  Phishing: {sum(y == 1)} ({100*sum(y == 1)/len(y):.1f}%)")
    
    # Test different hyperparameters to find better model
    param_grid = {
        'n_estimators': [150, 200],
        'max_depth': [7, 8, 9],
        'learning_rate': [0.05, 0.08, 0.1],
        'subsample': [0.8, 0.9],
        'colsample_bytree': [0.8, 0.9],
        'gamma': [0.5, 1.0, 2.0],
        'min_child_weight': [2, 3],
        'reg_lambda': [2.0, 3.0],
    }
    
    print("\n🔍 Grid Search for optimal hyperparameters...")
    print("   (This may take a few minutes)\n")
    
    xgb_base = XGBClassifier(
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss',
        verbosity=0
    )
    
    # Use smaller subset for grid search to save time
    grid_search = GridSearchCV(
        xgb_base,
        param_grid,
        cv=3,
        scoring='f1',
        n_jobs=1,
        verbose=1
    )
    
    grid_search.fit(X_scaled, y)
    
    print(f"\n✅ Best parameters found:")
    print(f"   {grid_search.best_params_}")
    print(f"   Best F1 Score: {grid_search.best_score_:.4f}\n")
    
    # Train final model with best parameters
    best_model = grid_search.best_estimator_
    best_model.fit(X_scaled, y)
    
    # Evaluate with cross-validation
    print("📊 Cross-Validation Results:")
    scoring = {
        'accuracy': 'accuracy',
        'f1': 'f1',
        'precision': 'precision',
        'recall': 'recall',
        'roc_auc': 'roc_auc'
    }
    
    cv_results = cross_validate(
        best_model, X_scaled, y,
        cv=cv_splitter,
        scoring=scoring,
        return_train_score=True,
        n_jobs=1
    )
    
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
        print(f"    Gap:   {gap:.4f} {'⚠️  OVERFITTING' if gap > 0.05 else '✓ OK'}\n")
    
    # Feature importance
    importance = best_model.feature_importances_
    feature_importance_dict = {
        name: float(imp) for name, imp in zip(feature_names, importance)
    }
    
    print("📊 Top 10 Most Important Features:")
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    for i, (name, imp) in enumerate(sorted_features[:10], 1):
        print(f"   {i:2d}. {name:35s} {imp:7.4f}")
    
    # Test on reference URLs
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
            
            prediction = best_model.predict(features_scaled)[0]
            probabilities = best_model.predict_proba(features_scaled)[0]
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
    
    print(f"Accuracy on reference set: {correct_predictions}/{len(test_cases)} ({100*correct_predictions/len(test_cases):.1f}%)")
    
    return best_model, scaler, avg_results, feature_importance_dict


def save_models(model, scaler, model_info, output_dir='models'):
    """Save trained model and scaler"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(output_dir, 'level1_xgboost_22features.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✅ Model saved: {model_path}")
    
    # Save scaler
    scaler_path = os.path.join(output_dir, 'level1_scaler_22features.pkl')
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved: {scaler_path}")
    
    # Save info
    info_path = os.path.join(output_dir, 'level1_model_info_22features.json')
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    print(f"✅ Model info saved: {info_path}")


def main():
    """Main training pipeline"""
    
    print("\n" + "=" * 70)
    print("RETRAINING LEVEL-1 PHISHING DETECTION MODEL")
    print("With Optimized Hyperparameters")
    print("=" * 70 + "\n")
    
    dataset_path = '../datasets/PhiUSIIL_Phishing_URL_Dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    # Extract features
    X, y = extract_features_from_dataset(dataset_path)
    
    # Train with optimization
    model, scaler, cv_results, feature_importance = train_optimized_model(X, y)
    
    # Save models
    model_info = {
        'model_type': 'xgboost',
        'n_features': 22,
        'feature_names': get_feature_names(),
        'feature_importance': feature_importance,
        'cross_val_results': {
            metric: {k: float(v) for k, v in vals.items()}
            for metric, vals in cv_results.items()
        },
        'trained_at': datetime.now().isoformat()
    }
    
    save_models(model, scaler, model_info)
    
    print("\n" + "=" * 70)
    print("✅ RETRAINING COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
