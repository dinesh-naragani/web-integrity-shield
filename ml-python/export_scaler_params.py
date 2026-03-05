"""
Export StandardScaler parameters to JSON for Java backend to use
"""

import pickle
import json
import numpy as np

# Load scaler
with open('models/level1_scaler_22features.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Extract parameters
scaler_params = {
    'mean': scaler.mean_.tolist(),  # shape: [22]
    'scale': scaler.scale_.tolist(),  # shape: [22]
    'n_features': int(scaler.n_features_in_),
    'with_mean': bool(scaler.with_mean),
    'with_std': bool(scaler.with_std)
}

# Save to JSON
with open('models/level1_scaler_params.json', 'w') as f:
    json.dump(scaler_params, f, indent=2)

print("✅ Scaler parameters exported to level1_scaler_params.json")
print(f"\nScaler Configuration:")
print(f"  Features: {scaler_params['n_features']}")
print(f"  With Mean: {scaler_params['with_mean']}")
print(f"  With Std: {scaler_params['with_std']}")
print(f"\nMean values (first 5): {scaler_params['mean'][:5]}")
print(f"Scale values (first 5): {scaler_params['scale'][:5]}")

# Verify by scaling a test feature
test_feature = np.array([58.0, 10.0, 3.0, 0.0, 1.0, 1.0, 14.0, 5.0, 0.0, 0.0, 0.0, 2.0, 0.24, 0.09, 0.29, 2.0, 4.42, 0.0, 0.0, 0.0, 1.0, 1.0])
test_feature_array = np.array([test_feature])
scaled = scaler.transform(test_feature_array)[0]

print(f"\nTest: Scaling a 22-feature vector")
print(f"  Raw feature (first 5): {test_feature[:5]}")
print(f"  Scaled feature (first 5): {scaled[:5]}")
print(f"\nFormula: scaled = (raw - mean) / scale")
print(f"  Example for feature 0: ({test_feature[0]:.2f} - {scaler_params['mean'][0]:.2f}) / {scaler_params['scale'][0]:.4f} = {scaled[0]:.4f}")
