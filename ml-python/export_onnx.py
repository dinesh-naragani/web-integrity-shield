#!/usr/bin/env python3
"""Export best trained model to production format"""

import json
import pickle
import numpy as np
import onnxruntime as ort
from feature_extractor import extract_features
import os

print("=" * 80)
print("📦 MODEL EXPORT FOR PRODUCTION (PhiUSIIL Multi-Column Features)")
print("=" * 80)

# Load PhiUSIIL model config
with open('models/phiusiil_best_model_config.json', 'r') as f:
    config = json.load(f)

best_model_name = config['best_model']
print(f"\n🎯 Best Model: {best_model_name.upper()}")
print(f"   F1-Score: {config['metrics']['f1']:.4f}")
print(f"   Accuracy: {config['metrics']['accuracy']:.4f}")
print(f"   ROC-AUC: {config['metrics']['roc_auc']:.4f}")
print(f"   Dataset: {config['dataset']['source']}")
print(f"   Features: {config['features']['count']} columns from website content")

# Load PhiUSIIL models
with open('models/phiusiil_trained_models.pkl', 'rb') as f:
    data = pickle.load(f)
    models = data['models']
    scaler = data.get('scaler', None)
    feature_names = data.get('feature_columns', config['features']['names'])

best_model = models[best_model_name]

# Save as production pickle (XGBoost native format works best)
print(f"\n📝 Saving {best_model_name} as production model...")

prod_file = 'models/production_model.pkl'
with open(prod_file, 'wb') as f:
    pickle.dump({
        'model': best_model,
        'scaler': scaler,
        'model_type': best_model_name,
        'feature_names': feature_names,
        'source_dataset': 'PhiUSIIL_Phishing_URL_Dataset.csv',
        'feature_count': len(feature_names),
        'training_note': 'Multi-column website features from PhiUSIIL dataset (F1=1.0, Accuracy=1.0)'
    }, f)

file_size = os.path.getsize(prod_file) / 1024 / 1024
print(f"✓ {prod_file} ({file_size:.2f} MB)")


# Test inference - NOTE: PhiUSIIL features require real website content extraction
print(f"\n🧪 Model Loaded (PhiUSIIL features from website content)")
print(f"   Note: Feature extraction requires live website analysis")
print(f"   Level-1 will use URL-only features for quick screening")
print(f"   Level-2 will extract full PhiUSIIL features for deep analysis")

# Save metadata
print(f"\n💾 Saving Production Metadata...")

metadata = {
    'model_type': best_model_name,
    'framework': 'xgboost' if best_model_name == 'xgboost' else 'lightgbm',
    'source': 'PhiUSIIL_Phishing_URL_Dataset.csv',
    'metrics': config['metrics'],
    'dataset_info': config['dataset'],
    'features': {
        'count': config['features']['count'],
        'names': feature_names,
        'preprocessor': 'StandardScaler' if scaler else 'None',
        'mean': scaler.mean_.tolist() if scaler and hasattr(scaler, 'mean_') else None,
        'scale': scaler.scale_.tolist() if scaler and hasattr(scaler, 'scale_') else None,
        'note': 'Multi-column features extracted from website content during Level-2 analysis'
    },
    'model_config': {
        'input_features': config['features']['count'],
        'output_classes': 2,
        'threshold': 0.5,
        'risk_levels': {
            'low': [0.0, 0.3],
            'medium': [0.3, 0.7],
            'high': [0.7, 1.0]
        },
        'usage': 'Level-2 Deep Analysis (triggered when Level-1 score >= 0.7)'
    }
}

with open('models/production_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("  ✓ production_metadata.json")

print(f"\n✅ Export Complete!")
print(f"📁 Production files in ./models/")
print(f"   - production_model.pkl ({file_size:.2f} MB)")
print(f"   - production_metadata.json")
print(f"\n✨ PhiUSIIL Model Ready for Level-2 Deployment!")
print(f"\n📋 Architecture:")
print(f"   Level-1: URL-only features (7 features) → Quick screening")
print(f"   Level-2: Website content features (50 features) → Deep analysis")
print(f"   Trigger: When Level-1 risk score >= 0.7")

