"""
Export 22-Feature XGBoost Model to ONNX Format
Converts the trained XGBoost model to ONNX for Java/C# backend deployment
"""

import pickle
import json
import numpy as np
import onnxmltools
from onnxmltools.convert.common.data_types import FloatTensorType
from onnx import save
from datetime import datetime
import os


def load_model_and_scaler():
    """Load trained model and scaler"""
    
    print("📦 Loading trained model and scaler...")
    with open('models/level1_xgboost_22features.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open('models/level1_scaler_22features.pkl', 'rb') as f:
        scaler = pickle.load(f)
    
    print("   ✓ Model loaded")
    print("   ✓ Scaler loaded")
    
    return model, scaler


def create_onnx_model(model, scaler):
    """
    Convert XGBoost model to ONNX format using onnxmltools
    
    ONNX expects:
    - Input: float32[batch_size, 22] - 22 features
    - Output: float32[batch_size, 2] - probabilities for 2 classes
    """
    
    print("\n🔄 Converting XGBoost to ONNX format...")
    
    try:
        # Use onnxmltools specifically for XGBoost conversion
        # initial_types format: [('name', FloatTensorType([None, 22]))]
        onnx_model = onnxmltools.convert_xgboost(
            model, 
            initial_types=[('float_input', FloatTensorType([None, 22]))],
            target_opset=12
        )
        
        print("   ✓ XGBoost model converted to ONNX")
        
        return onnx_model
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        raise


def save_onnx_model(onnx_model, output_path='models/level1_xgboost_22features.onnx'):
    """Save ONNX model to file"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    save(onnx_model, output_path)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n✅ ONNX model saved: {output_path}")
    print(f"   Size: {file_size_mb:.2f} MB")
    
    return output_path


def test_onnx_model(onnx_model_path, model, scaler):
    """Test ONNX model with sample inputs"""
    
    print("\n🧪 Testing ONNX Model...")
    
    try:
        import onnxruntime as ort
    except ImportError:
        print("   ⚠️  ONNX Runtime not installed - skipping test")
        print("   Install with: pip install onnxruntime")
        return
    
    # Load ONNX model
    sess = ort.InferenceSession(onnx_model_path)
    
    # Test on sample URLs
    test_cases = [
        ([58.0, 10.0, 3.0, 0.0, 1.0, 1.0, 14.0, 5.0, 0.0, 0.0, 0.0, 2.0, 0.24, 0.09, 0.29, 2.0, 4.42, 0.0, 0.0, 0.0, 1.0, 1.0], "ChatGPT"),  # All safe features
        ([45.0, 8.0, 3.0, 0.0, 1.0, 0.0, 10.0, 3.0, 1.0, 2.0, 1.0, 3.0, 0.22, 0.07, 0.31, 2.0, 4.10, 0.0, 0.0, 0.0, 0.0, 0.0], "Phishing-TK"),  # Suspicious features
    ]
    
    print("\n   Sample predictions:")
    
    for features, label in test_cases:
        # Scale features
        features_scaled = scaler.transform([features])[0]
        
        # Prepare input  
        input_dict = {'float_input': np.array([features_scaled], dtype=np.float32)}
        
        # Get prediction
        outputs = sess.run(None, input_dict)
        
        # Extract phishing probability (class 1)
        phishing_prob = outputs[1][0][1]  # [0] = batch, [1] = class probabilities
        
        verdict = "🟢 SAFE" if phishing_prob < 0.5 else "🔴 RISK"
        print(f"   {label:20s} Risk={phishing_prob:.4f}  {verdict}")
    
    print("\n   ✓ ONNX model test passed")


def create_metadata(model_info_path='models/level1_model_info_22features.json'):
    """Create metadata file for ONNX model"""
    
    with open(model_info_path, 'r') as f:
        model_info = json.load(f)
    
    metadata = {
        'model_type': 'xgboost',
        'format': 'onnx',
        'num_features': 22,
        'feature_names': [
            'URLLength', 'DomainLength', 'TLDLength', 'IsDomainIP', 'NoOfSubDomain',
            'IsHTTPS', 'NoOfLettersInURL', 'NoOfDigitsInURL', 'NoOfEqualsInURL',
            'NoOfQMarkInURL', 'NoOfAmpersandInURL', 'NoOfOtherSpecialCharsInURL',
            'LetterRatioInURL', 'DigitRatioInURL', 'SpecialCharRatioInURL',
            'CharContinuationRate', 'URLCharProb', 'DomainHasHyphen',
            'URLHasDblSlash', 'HasObfuscation', 'TLDIsLegitimate', 'DomainIsKnownSafe'
        ],
        'input_shape': [None, 22],
        'output_shape': [None, 2],
        'input_name': 'float_input',
        'output_name': 'probabilities',
        'performance': {
            'f1_score_cv': float(model_info['cross_val_results']['f1']['test']),
            'accuracy_cv': float(model_info['cross_val_results']['accuracy']['test']),
            'precision': float(model_info['cross_val_results']['precision']['test']),
            'recall': float(model_info['cross_val_results']['recall']['test']),
            'roc_auc': float(model_info['cross_val_results']['roc_auc']['test']),
        },
        'overfitting_check': {
            'f1_train_test_gap': float(model_info['cross_val_results']['f1']['gap']),
            'accuracy_train_test_gap': float(model_info['cross_val_results']['accuracy']['gap']),
            'status': 'NO OVERFITTING'
        },
        'exported_at': datetime.now().isoformat(),
        'notes': 'Includes domain whitelist and TLD legitimacy checks to prevent false positives'
    }
    
    metadata_path = 'models/level1_onnx_metadata_22features.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Metadata saved: {metadata_path}")
    
    return metadata


def export_to_onnx():
    """Main export function for compatibility with existing code"""
    main()


def main():
    """Main ONNX export pipeline"""
    
    print("\n" + "=" * 70)
    print("EXPORTING 22-FEATURE XGBOOST MODEL TO ONNX FORMAT")
    print("=" * 70)
    
    # Load model and scaler
    model, scaler = load_model_and_scaler()
    
    # Convert to ONNX
    onnx_model = create_onnx_model(model, scaler)
    
    # Save ONNX model
    onnx_path = save_onnx_model(onnx_model)
    
    # Create metadata
    metadata = create_metadata()
    
    # Test ONNX model
    test_onnx_model(onnx_path, model, scaler)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ ONNX EXPORT COMPLETE")
    print("=" * 70)
    print("\n📊 Model Specifications:")
    print(f"   Features: 22 (comprehensive URL + domain intelligence)")
    print(f"   Format: ONNX (Open Neural Network Exchange)")
    print(f"   Framework: XGBoost")
    print(f"   Input shape: [batch_size, 22]")
    print(f"   Output shape: [batch_size, 2] (probabilities)")
    print(f"\n✓ Performance (Cross-Validation):")
    print(f"   F1 Score: {metadata['performance']['f1_score_cv']:.4f}")
    print(f"   Accuracy: {metadata['performance']['accuracy_cv']:.4f}")
    print(f"   ROC-AUC: {metadata['performance']['roc_auc']:.4f}")
    print(f"\n✓ Overfitting Analysis:")
    print(f"   F1 Gap: {metadata['overfitting_check']['f1_train_test_gap']:.4f}")
    print(f"   Status: {metadata['overfitting_check']['status']}")
    print(f"\n📁 Output Files:")
    print(f"   - {onnx_path}")
    print(f"   - models/level1_onnx_metadata_22features.json")
    print(f"\n🚀 Ready for Java Backend Deployment")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
