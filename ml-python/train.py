"""
Train Level-1 Phishing Detection Model

This script:
1. Loads/creates training dataset (phishing + legitimate URLs)
2. Extracts features using feature_extractor.py
3. Trains Logistic Regression model
4. Evaluates model performance
5. Saves trained model as .pkl

Dataset split: 70% train, 15% validation, 15% test
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from feature_extractor import extract_features, get_feature_names, validate_features
import json


# Real legitimate URLs from top domains
# These represent safe, trusted websites
# Expanded list for better training balance
LEGITIMATE_URLS = [
    # Tech companies
    'https://www.google.com',
    'https://www.microsoft.com',
    'https://www.apple.com',
    'https://www.amazon.com',
    'https://www.github.com',
    'https://stackoverflow.com',
    'https://www.wikipedia.org',
    'https://www.youtube.com',
    'https://www.linkedin.com',
    'https://www.twitter.com',
    'https://www.facebook.com',
    'https://www.instagram.com',
    'https://www.reddit.com',
    'https://www.github.com/features',
    'https://docs.python.org',
    'https://www.w3schools.com',
    'https://www.udemy.com',
    'https://www.coursera.org',
    'https://www.netflix.com',
    'https://www.spotify.com',
    # Banking/Finance
    'https://www.bofa.com',
    'https://www.chase.com',
    'https://www.wellsfargo.com',
    'https://www.citadel.com',
    'https://www.paypal.com',
    'https://www.wise.com',
    'https://www.stripe.com',
    'https://www.coinbase.com',
    # News/Media
    'https://www.bbc.com',
    'https://www.cnn.com',
    'https://www.reuters.com',
    'https://www.theguardian.com',
    'https://www.nytimes.com',
    # E-commerce
    'https://www.ebay.com',
    'https://www.alibaba.com',
    'https://www.shopify.com',
    'https://www.etsy.com',
    # Social/Communication
    'https://www.slack.com',
    'https://www.zoom.us',
    'https://www.discord.com',
    'https://www.telegram.org',
    # Additional trusted sites
    'https://www.mozilla.org',
    'https://www.openssl.org',
    'https://www.gnu.org',
    'https://www.linux.org',
    'https://www.apache.org',
    'https://www.nginx.org',
    'https://www.rust-lang.org',
    'https://golang.org',
    'https://nodejs.org',
    'https://www.oracle.com',
    'https://www.ibm.com',
    'https://www.intel.com',
    'https://www.hp.com',
    'https://www.dell.com',
    'https://www.lenovo.com',
]


def load_dataset():
    """
    Load or create training dataset.
    
    Returns:
        DataFrame with columns: ['url', 'label']
        label: 1 = phishing, 0 = legitimate
    """
    
    dataset_path = 'dataset.csv'
    
    print(f"Loading PhishTank dataset from {dataset_path}...")
    
    # Load PhishTank CSV (from repository root)
    phishtank_path = '../dataset.csv'
    
    if os.path.exists(phishtank_path):
        # Load PhishTank data
        print(f"  Reading PhishTank CSV (56K+ URLs)...")
        phish_df = pd.read_csv(phishtank_path)
        phishing_urls = phish_df['url'].tolist()
        print(f"✓ Loaded {len(phishing_urls)} phishing URLs from PhishTank")
        
        # Use MAXIMUM data available for training
        # RTX 3060 can handle 10K+ URLs easily
        sample_size = min(10000, len(phishing_urls))  # Use up to 10K phishing URLs
        phishing_urls = phishing_urls[:sample_size]
        print(f"  Using {sample_size} phishing URLs for training (GPU-accelerated)")
    else:
        print(f"⚠ PhishTank dataset not found at {phishtank_path}")
        phishing_urls = []
    
    # Add legitimate URLs (expanded list)
    legitimate_urls = LEGITIMATE_URLS
    print(f"✓ Using {len(legitimate_urls)} legitimate URLs")
    
    # Create balanced dataset
    # Use 2:1 ratio (phishing:legitimate) which is realistic for security
    if len(phishing_urls) > 0:
        phishing_sample = phishing_urls[:len(legitimate_urls) * 40]  # 40:1 ratio for realistic imbalance
        phishing_sample = phishing_urls[:min(len(phishing_urls), 10000)]  # Cap at 10K
    else:
        phishing_sample = []
    
    # Create dataset - MUCH LARGER now
    phishing_data = [{'url': url, 'label': 1} for url in phishing_sample]
    
    # Replicate legitimate URLs to create balance
    # Duplicate legitimate URLs to balance against phishing URLs
    legitimate_sample = []
    while len(legitimate_sample) < min(len(phishing_sample) // 20, 5000):  # Up to 5K legit URLs
        legitimate_sample.extend(legitimate_urls)
    legitimate_sample = legitimate_sample[:min(len(phishing_sample) // 20, 5000)]
    
    legitimate_data = [{'url': url, 'label': 0} for url in legitimate_sample]
    
    dataset = phishing_data + legitimate_data
    df = pd.DataFrame(dataset)
    
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    print(f"\nDataset composition:")
    print(f"  Phishing (label=1): {len(phishing_data)} URLs")
    print(f"  Legitimate (label=0): {len(legitimate_data)} URLs")
    print(f"  Total: {len(df)} URLs")
    print(f"  Ratio: {len(phishing_data)/len(legitimate_data):.1f}:1 (realistic imbalance)")
    
    return df


def extract_dataset_features(urls, labels):
    """
    Extract features from all URLs in dataset.
    
    Returns:
        Tuple of (X, y) where X is features array, y is labels
    """
    X = []
    y = []
    invalid_count = 0
    
    for url, label in zip(urls, labels):
        try:
            features, _ = extract_features(url)
            
            # Validate features
            if not validate_features(features):
                print(f"Warning: Invalid features for URL: {url}")
                invalid_count += 1
                continue
            
            X.append(features)
            y.append(label)
        except Exception as e:
            print(f"Error extracting features from {url}: {e}")
            invalid_count += 1
            continue
    
    if invalid_count > 0:
        print(f"Skipped {invalid_count} URLs due to errors")
    
    return np.array(X), np.array(y)


def train_model(X_train, y_train, model_type='random_forest'):
    """
    Train phishing detection model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        model_type: 'logistic_regression' or 'random_forest'
        
    Returns:
        Trained model
    """
    
    # Use Random Forest for better performance with larger datasets
    if model_type == 'logistic_regression':
        print("Training Logistic Regression model...")
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1  # Use all CPU cores
        )
    elif model_type == 'random_forest':
        print("Training Random Forest model (with all available CPU cores)...")
        print(f"  Data size: {X_train.shape[0]} samples")
        model = RandomForestClassifier(
            n_estimators=200,           # Increased from 100
            max_depth=20,               # Increased from 15
            min_samples_split=5,        # Reduced for more complex trees
            min_samples_leaf=2,         # Reduced for more complex trees
            random_state=42,
            class_weight='balanced',
            n_jobs=-1,                  # Use all CPU cores
            verbose=1                   # Show training progress
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    print(f"Starting training...")
    model.fit(X_train, y_train)
    print(f"✓ Training complete")
    
    return model


def evaluate_model(model, X_val, y_val, X_test, y_test, set_name=''):
    """
    Evaluate model performance on validation and test sets.
    
    Returns:
        Dictionary with metrics
    """
    
    # Validation predictions
    y_val_pred = model.predict(X_val)
    y_val_proba = model.predict_proba(X_val)[:, 1]
    
    # Test predictions
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'validation': {
            'accuracy': accuracy_score(y_val, y_val_pred),
            'precision': precision_score(y_val, y_val_pred, zero_division=0),
            'recall': recall_score(y_val, y_val_pred, zero_division=0),
            'f1': f1_score(y_val, y_val_pred, zero_division=0),
            'confusion_matrix': confusion_matrix(y_val, y_val_pred).tolist()
        },
        'test': {
            'accuracy': accuracy_score(y_test, y_test_pred),
            'precision': precision_score(y_test, y_test_pred, zero_division=0),
            'recall': recall_score(y_test, y_test_pred, zero_division=0),
            'f1': f1_score(y_test, y_test_pred, zero_division=0),
            'confusion_matrix': confusion_matrix(y_test, y_test_pred).tolist()
        }
    }
    
    print(f"\n{'='*60}")
    print(f"Model Evaluation Results {set_name}")
    print(f"{'='*60}")
    print(f"\nVALIDATION SET:")
    print(f"  Accuracy:  {metrics['validation']['accuracy']:.4f}")
    print(f"  Precision: {metrics['validation']['precision']:.4f}")
    print(f"  Recall:    {metrics['validation']['recall']:.4f}")
    print(f"  F1-Score:  {metrics['validation']['f1']:.4f}")
    print(f"\nTEST SET:")
    print(f"  Accuracy:  {metrics['test']['accuracy']:.4f}")
    print(f"  Precision: {metrics['test']['precision']:.4f}")
    print(f"  Recall:    {metrics['test']['recall']:.4f}")
    print(f"  F1-Score:  {metrics['test']['f1']:.4f}")
    print(f"\nConfusion Matrix (Test):")
    print(f"  True Negatives:  {metrics['test']['confusion_matrix'][0][0]}")
    print(f"  False Positives: {metrics['test']['confusion_matrix'][0][1]}")
    print(f"  False Negatives: {metrics['test']['confusion_matrix'][1][0]}")
    print(f"  True Positives:  {metrics['test']['confusion_matrix'][1][1]}")
    print(f"{'='*60}\n")
    
    return metrics


def save_model(model, model_path='url_model.pkl'):
    """
    Save trained model to pickle file.
    """
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {model_path}")


def save_metrics(metrics, metrics_path='model_metrics.json'):
    """
    Save evaluation metrics to JSON file.
    """
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {metrics_path}")


def save_feature_config(feature_names, config_path='feature_config.json'):
    """
    Save feature names and configuration for later reference.
    Important: must match Java implementation.
    """
    config = {
        'version': '1.0',
        'feature_names': feature_names,
        'num_features': len(feature_names),
        'threshold': 0.7  # Deep analysis trigger threshold
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Feature config saved to {config_path}")


def main():
    """
    Main training pipeline with expanded dataset and timing.
    """
    
    import time
    
    print("="*70)
    print("Web Integrity Shield - Level-1 Model Training (EXPANDED DATASET)")
    print("="*70)
    print()
    
    start_time = time.time()
    
    # Step 1: Load dataset
    df = load_dataset()
    print(f"Dataset size: {len(df)} URLs")
    print(f"  Phishing: {(df['label'] == 1).sum()}")
    print(f"  Legitimate: {(df['label'] == 0).sum()}\n")
    
    # Step 2: Extract features
    print("Extracting features from URLs (deterministic)...")
    t0 = time.time()
    X, y = extract_dataset_features(df['url'].values, df['label'].values)
    t_features = time.time() - t0
    print(f"Features extracted: {X.shape} in {t_features:.2f}s")
    print(f"Feature names: {get_feature_names()}\n")
    
    # Step 3: Split dataset (70% train, 15% val, 15% test)
    print("Splitting dataset...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    
    print(f"Data split:")
    print(f"  Training: {len(X_train)} URLs")
    print(f"  Validation: {len(X_val)} URLs")
    print(f"  Test: {len(X_test)} URLs\n")
    
    # Step 4: Train model (Random Forest for larger dataset)
    print("=" * 70)
    t0 = time.time()
    model = train_model(X_train, y_train, model_type='random_forest')
    t_train = time.time() - t0
    print(f"Training completed in {t_train:.2f}s\n")
    print("=" * 70)
    
    # Step 5: Evaluate model
    metrics = evaluate_model(model, X_val, y_val, X_test, y_test)
    
    # Step 6: Save model and config
    save_model(model)
    save_metrics(metrics)
    save_feature_config(get_feature_names())
    
    total_time = time.time() - start_time
    
    print("="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Feature extraction: {t_features:.2f}s")
    print(f"Model training: {t_train:.2f}s")
    print(f"Total time: {total_time:.2f}s")
    print(f"\nNext step: Run export_onnx.py to convert model to binary format")


if __name__ == '__main__':
    main()
