"""
Standalone ONNX Model Conversion Script
Converts trained sklearn model to ONNX format for Java backend
"""

import os
import sys
import pickle
import json

def check_and_install_dependencies():
    """Check ONNX dependencies and attempt to install if missing"""
    print("Checking ONNX dependencies...")
    
    try:
        import skl2onnx
        import onnx
        import onnxruntime
        print("✓ All ONNX packages are available")
        return True
    except ImportError as e:
        print(f"⚠ Missing ONNX packages: {e}")
        print("\nAttempting to install...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "skl2onnx", "onnx", "onnxruntime", "-q"])
            print("✓ ONNX packages installed successfully")
            return True
        except Exception as install_err:
            print(f"✗ Failed to install: {install_err}")
            return False


def main():
    print("=" * 70)
    print("Web Integrity Shield - ONNX Model Conversion")
    print("=" * 70)
    print()
    
    # Check dependencies
    if not check_and_install_dependencies():
        print("\n✗ Cannot proceed without ONNX dependencies")
        print("Please install manually:")
        print("  pip install skl2onnx onnx onnxruntime")
        return False
    
    try:
        # Import ONNX tools
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        import onnx
        import numpy as np
        
        # Load model
        model_path = 'url_model.pkl'
        if not os.path.exists(model_path):
            print(f"✗ Model not found: {model_path}")
            return False
        
        print(f"Loading model from {model_path}...")
        with open(model_path, 'rb') as f:
            sklearn_model = pickle.load(f)
        print("✓ Model loaded successfully")
        
        # Prepare ONNX conversion
        print("\nPreparing ONNX conversion...")
        num_features = 7
        initial_type = [('float_input', FloatTensorType([None, num_features]))]
        
        # Convert to ONNX
        print(f"Converting to ONNX format (features: {num_features})...")
        onnx_model = convert_sklearn(sklearn_model, initial_types=initial_type)
        
        # Create models directory
        os.makedirs('models', exist_ok=True)
        
        # Save ONNX model
        onnx_path = os.path.join('models', 'url_model.onnx')
        onnx.save_model(onnx_model, onnx_path)
        print(f"✓ ONNX model saved to {onnx_path}")
        
        # Validate ONNX model
        print("\nValidating ONNX model...")
        onnx.checker.check_model(onnx_model)
        print("✓ ONNX model structure is valid")
        
        # Test inference with ONNX
        print("\nTesting ONNX inference...")
        import onnxruntime as rt
        from feature_extractor import extract_features, validate_features
        
        sess = rt.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        input_name = sess.get_inputs()[0].name
        output_names = [o.name for o in sess.get_outputs()]
        
        test_urls = [
            'https://www.google.com',
            'https://paypal-login-verify.com'
        ]
        
        print(f"Testing {len(test_urls)} URLs...")
        for url in test_urls:
            features, _ = extract_features(url)
            if not validate_features(features):
                print(f"✗ Invalid features for {url}")
                continue
                
            X = np.array([features], dtype=np.float32)
            results = sess.run(output_names, {input_name: X})
            
            # Extract probability from output
            if len(results) > 1:
                # Multi-output: [label, probabilities]
                prob = results[1][0, 1]
            else:
                # Single output
                prob = results[0][0, 1] if len(results[0].shape) > 1 else results[0][0]
            
            label = "PHISHING" if prob > 0.5 else "LEGITIMATE"
            print(f"✓ {url[:45]:<45} Risk: {prob:.4f} ({label})")
        
        print("\n" + "=" * 70)
        print("✓ ONNX CONVERSION SUCCESSFUL")
        print("=" * 70)
        print(f"\nONNX Model Details:")
        print(f"  File: models/url_model.onnx")
        print(f"  Input features: {num_features}")
        print(f"  Input tensor shape: [batch_size, {num_features}]")
        print(f"  Output: Probability (0-1)")
        print(f"  Threshold for deep analysis: 0.7")
        print(f"\n✓ Ready for Java backend integration")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
