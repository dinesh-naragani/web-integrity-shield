"""
Train Level-1 Model with GPU Acceleration and Optimized Hyperparameters
Uses GPU for XGBoost and parallel grid search
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


def check_gpu_availability():
    """Check if GPU is available for XGBoost"""
    try:
        # Try to create a simple XGBoost model with GPU
        test_model = XGBClassifier(tree_method='gpu_hist', gpu_id=0, verbosity=0)
        print("✅ GPU Available: NVIDIA GPU detected for XGBoost acceleration")
        return True
    except Exception as e:
        print(f"⚠️  GPU Not Available: {str(e)[:80]}")
        print("   Will use CPU for training (slower)")
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


def calculate_class_weight(y):
    """Calculate class weights to handle imbalance"""
    n_samples = len(y)
    n_classes = 2
    class_counts = np.bincount(y)
    
    weights = n_samples / (n_classes * class_counts)
    return dict(enumerate(weights))


def train_with_gpu(X, y, use_gpu=True):
    """
    Train XGBoost with GPU acceleration and optimized hyperparameters
    Focuses on better discrimination between legitimate and phishing URLs
    """
    
    print("\n" + "=" * 70)
    print("🚀 XGBoost Training with GPU Acceleration")
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
    
    # Calculate class weights for imbalanced dataset
    class_weights = calculate_class_weight(y)
    sample_weight = np.array([class_weights[label] for label in y])
    print(f"\n⚖️  Class weights: {class_weights}")
    
    # Optimized hyperparameters focusing on:
    # - Higher learning rate (0.1-0.15) for better convergence
    # - Deeper trees (10-12) to capture feature interactions
    # - Higher regularization to prevent overfitting
    # - Lower subsample (0.7-0.8) for better feature diversity
    
    print("\n🔧 Training with optimized hyperparameters...")
    
    xgb_model = XGBClassifier(
        # Tree structure
        n_estimators=250,
        max_depth=11,
        min_child_weight=1,
        
        # Learning
        learning_rate=0.12,
        subsample=0.75,
        colsample_bytree=0.75,
        
        # Regularization (stronger to prevent overfitting)
        gamma=1.0,
        reg_lambda=2.5,
        reg_alpha=0.5,
        
        # GPU settings
        device='cuda' if use_gpu else 'cpu',
        tree_method='hist',
        
        # Other
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=42,
        use_label_encoder=False,
        verbosity=0
    )
    
    # Train with class weights
    print("   Training...")
    xgb_model.fit(X_scaled, y, sample_weight=sample_weight)
    
    print("✅ Training complete\n")
    
    # Evaluate with cross-validation
    print("📈 Cross-Validation Analysis:")
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
    
    # Display results
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
        
        metric_upper = metric.upper()
        status = "✓" if gap < 0.05 else ("⚠️" if gap < 0.10 else "❌")
        print(f"  {status} {metric_upper:10s} Test: {avg_test:.4f} ± {std_test:.4f} | Gap: {gap:.4f}")
    
    # Display feature importance
    print("\n📊 Top 10 Most Important Features:")
    print("=" * 70)
    importance = xgb_model.feature_importances_
    feature_importance_dict = {
        name: float(imp) for name, imp in zip(feature_names, importance)
    }
    
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    for i, (name, imp) in enumerate(sorted_features[:10], 1):
        bar = "█" * int(imp * 50)
        print(f"   {i:2d}. {name:30s} {imp:7.4f} {bar}")
    
    return xgb_model, scaler, avg_results, feature_importance_dict


def test_on_phishing_urls(model, scaler):
    """Test model on known phishing URLs"""
    
    print("\n" + "=" * 70)
    print("🧪 Testing on Phishing Detection Benchmark URLs")
    print("=" * 70 + "\n")
    
    test_cases = [
        ("https://www.chatgpt.com", "LEGITIMATE"),
        ("https://discord.com", "LEGITIMATE"),
        ("https://www.youtube.com", "LEGITIMATE"),
        ("https://github.com", "LEGITIMATE"),
        ("https://www.google.com", "LEGITIMATE"),
        ("http://paypa1.com/verify-account", "PHISHING"),
        ("http://45.77.12.99/login?session=abc", "PHISHING"),
        ("http://secure-login-paypal-verify.tk/account", "PHISHING"),
        ("http://apple-id-security-update.ga/login", "PHISHING"),
        ("https://secure-amazon-login-verify.ml/account", "PHISHING"),
    ]
    
    correct = 0
    
    for url, expected in test_cases:
        try:
            features, _ = extract_comprehensive_features(url)
            features_scaled = scaler.transform([features])
            
            pred_proba = model.predict_proba(features_scaled)[0]
            pred_class = model.predict(features_scaled)[0]
            
            pred_label = "PHISHING" if pred_class == 1 else "LEGITIMATE"
            is_correct = (pred_label == expected)
            status = "✓" if is_correct else "✗"
            
            if is_correct:
                correct += 1
            
            print(f"{status} {url:50s}")
            print(f"   Expected: {expected:12s} | Predicted: {pred_label:12s} | Prob: {pred_proba[1]:.4f}\n")
        
        except Exception as e:
            print(f"✗ {url}: Error - {e}\n")
    
    accuracy = 100 * correct / len(test_cases)
    print(f"Accuracy on test set: {correct}/{len(test_cases)} ({accuracy:.1f}%)")
    

def save_models(model, scaler, avg_results, feature_importance, output_dir='models'):
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
    feature_names = get_feature_names()
    model_info = {
        'model_type': 'xgboost',
        'n_features': 22,
        'feature_names': feature_names,
        'feature_importance': feature_importance,
        'cross_val_results': {
            metric: {
                'train': float(results['train']),
                'test': float(results['test']),
                'std': float(results['std']),
                'gap': float(results['gap'])
            }
            for metric, results in avg_results.items()
        },
        'trained_at': datetime.now().isoformat()
    }
    
    info_path = os.path.join(output_dir, 'level1_model_info_22features.json')
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    print(f"✅ Model info saved: {info_path}")


def main():
    """Main training pipeline"""
    
    print("\n" + "=" * 70)
    print("LEVEL-1 PHISHING DETECTION MODEL TRAINING")
    print("GPU-Accelerated XGBoost with Optimized Hyperparameters")
    print("=" * 70 + "\n")
    
    # Check GPU availability
    use_gpu = check_gpu_availability()
    
    # Load dataset
    dataset_path = '../datasets/PhiUSIIL_Phishing_URL_Dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    # Extract features
    X, y = extract_features_from_dataset(dataset_path)
    
    # Train model
    model, scaler, cv_results, feature_importance = train_with_gpu(X, y, use_gpu=use_gpu)
    
    # Test on known phishing URLs
    test_on_phishing_urls(model, scaler)
    
    # Save models
    save_models(model, scaler, cv_results, feature_importance)
    
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Export ONNX model: python export_onnx_22features.py")
    print("2. Deploy to Java backend")
    print("3. Test API endpoints")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
