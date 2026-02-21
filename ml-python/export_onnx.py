"""
Export Trained Model for Backend Integration

This script:
1. Loads the trained pickle model
2. Validates model and features
3. Tests inference consistency
4. Prepares model for Java/backend integration
5. Saves feature configuration for matching

Note: ONNX export is optional. The pickled model with feature config 
is sufficient for Java integration via direct pickle loading or REST API conversion.
"""

import os
import pickle
import json
import numpy as np
from feature_extractor import extract_features, get_feature_names, validate_features


def load_trained_model(model_path='url_model.pkl'):
    """
    Load the pickled trained model.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            f"Run train.py first to train the model."
        )
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"✓ Loaded model from {model_path}")
    return model


def export_to_onnx(sklearn_model, num_features=7, onnx_path='url_model.onnx'):
    """
    NOTE: ONNX export requires skl2onnx with intact installation.
    For now, we save the pickled model directly.
    
    The pickled model can be:
    1. Used directly via Python pickle in backend
    2. Converted to ONNX separately if needed
    3. Wrapped in a REST API endpoint
    
    Args:
        sklearn_model: Trained sklearn model
        num_features: Number of input features
        onnx_path: Output path (for reference)
    """
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Copy the pickled model to models folder
    import shutil
    src_model = 'url_model.pkl'
    dst_model = os.path.join('models', 'url_model.pkl')
    
    if os.path.exists(src_model):
        shutil.copy(src_model, dst_model)
        print(f"✓ Model copied to {dst_model}")
    
    # Also save model summary
    model_summary = {
        'type': 'LogisticRegression',
        'framework': 'scikit-learn',
        'input_features': num_features,
        'output': 'probability_score (0-1)',
        'notes': 'ONNX export can be done separately if needed'
    }
    
    summary_path = os.path.join('models', 'model_info.json')
    with open(summary_path, 'w') as f:
        json.dump(model_summary, f, indent=2)
    print(f"✓ Model info saved to {summary_path}")
    
    return dst_model


def validate_model(sklearn_model):
    """
    Validate the trained sklearn model.
    """
    print(f"Validating model...")
    
    # Check model has required methods
    if not hasattr(sklearn_model, 'predict'):
        raise ValueError("Model missing predict method")
    if not hasattr(sklearn_model, 'predict_proba'):
        raise ValueError("Model missing predict_proba method")
    
    print(f"✓ Model is valid (has predict and predict_proba methods)")
    
    # Model info
    model_class = sklearn_model.__class__.__name__
    print(f"  Model type: {model_class}")
    
    return True


def test_inference(sklearn_model, test_urls):
    """
    Test sklearn model inference.
    
    Args:
        sklearn_model: Trained sklearn model
        test_urls: List of test URLs
    """
    
    print(f"\nTesting model inference on {len(test_urls)} test URLs...")
    print("-" * 70)
    
    all_valid = True
    results = []
    
    for url in test_urls:
        try:
            # Extract features
            features, feature_dict = extract_features(url)
            if not validate_features(features):
                print(f"✗ Invalid features for: {url}")
                all_valid = False
                continue
            
            # Prepare input
            X_test = np.array([features], dtype=np.float32)
            
            # sklearn prediction
            prediction = sklearn_model.predict(X_test)[0]
            probability = sklearn_model.predict_proba(X_test)[0, 1]
            
            # Determine label
            label = "PHISHING" if prediction == 1 else "LEGITIMATE"
            
            results.append({
                'url': url,
                'risk_score': probability,
                'prediction': prediction,
                'label': label
            })
            
            print(f"✓ {url[:50]:<50}")
            print(f"   Risk Score: {probability:.4f}, Label: {label}")
            
        except Exception as e:
            print(f"✗ Error processing {url}: {e}")
            all_valid = False
    
    print("-" * 70)
    
    if all_valid:
        print("✓ All URLs processed successfully!")
    else:
        print("⚠ Some URLs had errors")
    
    return results, all_valid


def verify_feature_consistency():
    """
    Verify that feature extraction is deterministic.
    Extract features from the same URL multiple times.
    """
    
    print("\nVerifying feature extraction determinism...")
    
    test_url = "https://www.paypal-login-verify.com/signin"
    
    features_list = []
    for i in range(5):
        features, _ = extract_features(test_url)
        features_list.append(features)
    
    # Check if all extractions are identical
    for i in range(1, len(features_list)):
        if not np.allclose(features_list[0], features_list[i]):
            print(f"✗ Feature extraction is NOT deterministic!")
            return False
    
    print(f"✓ Feature extraction is deterministic (tested 5 times)")
    print(f"  Features: {features_list[0]}")
    print(f"  Names: {get_feature_names()}")
    
    return True


def main():
    """
    Main export pipeline.
    """
    
    print("=" * 70)
    print("Web Integrity Shield - Model Export for Backend Integration")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Load trained model
        sklearn_model = load_trained_model()
        
        # Step 2: Verify feature consistency
        if not verify_feature_consistency():
            print("ERROR: Feature extraction must be deterministic!")
            return False
        
        # Step 3: Copy model to models folder and validate
        model_path = export_to_onnx(sklearn_model, num_features=7)
        
        # Step 4: Validate model
        if not validate_model(sklearn_model):
            print("ERROR: Model validation failed")
            return False
        
        # Step 5: Test inference
        test_urls = [
            'https://www.google.com',
            'http://192.168.1.1/admin',
            'https://paypal-login-verify.com',
            'http://bit.ly/phishing-click',
            'https://www.amazon.com'
        ]
        
        results, inference_ok = test_inference(sklearn_model, test_urls)
        
        if inference_ok:
            print("\n" + "=" * 70)
            print("✓ EXPORT SUCCESSFUL")
            print("=" * 70)
            print(f"\nModel ready for backend integration:")
            print(f"  Location: models/url_model.pkl")
            print(f"  Features: {get_feature_names()}")
            print(f"  Backend can load via:")
            print(f"    - Python pickle: pickle.load()")
            print(f"    - Java via: REST API to Python wrapper")
            print(f"    - ONNX: Can be converted separately if needed")
            print(f"\nNext step: Copy models/ folder to backend-java/models/")
        else:
            print("\n⚠ Export completed but some tests failed")
        
        return inference_ok
        
    except Exception as e:
        print(f"\n✗ Error during export: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
