import onnxruntime as ort
import numpy as np

sess = ort.InferenceSession('ml-python/models/level1_xgboost_22features.onnx')

print("ONNX Inputs:")
for i in sess.get_inputs():
    print(f"  {i.name}: shape={i.shape}")

print("\nONNX Outputs:")
for o in sess.get_outputs():
    print(f"  {o.name}: shape={o.shape}")

# Test with dummy features
test_features = np.random.randn(1, 22).astype(np.float32)
input_name = sess.get_inputs()[0].name
result = sess.run(None, {input_name: test_features})

print(f"\nTest Output:")
for i, out in enumerate(result):
    print(f"  Output {i}: shape={out.shape}, dtype={out.dtype}")
    print(f"           value={out}")
