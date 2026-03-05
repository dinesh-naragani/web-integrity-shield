package com.wsi.phishing.service;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;
import ai.onnxruntime.OnnxMap;
import ai.onnxruntime.OnnxSequence;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;
import jakarta.annotation.PostConstruct;

/**
 * ONNX Model Service for Level-1 Phishing Detection
 * 
 * Loads XGBoost model at application startup.
 * Provides synchronous inference on comprehensive URL features.
 * 
 * Model: url_model.onnx (ONNX format)
 * - Input: float[1, 22] (22 comprehensive URL features)
 * - Features include domain whitelist, TLD legitimacy, entropy, etc.
 * - Output: double (probability of phishing, 0.0-1.0)
 *   0.0 = Legitimate, 1.0 = Phishing
 */
@Service
public class OnnxModelService {

    private static final Logger log = LoggerFactory.getLogger(OnnxModelService.class);
    
    @Value("${onnx.model.path:classpath:models/url_model.onnx}")
    private String modelPath;
    
    private OrtEnvironment ortEnvironment;
    private OrtSession ortSession;
    
    // Scaler parameters for feature normalization
    private double[] scalerMean;
    private double[] scalerScale;
    private int nFeatures = 22;
    
    /**
     * Initialize ONNX Runtime environment and load model at startup
     */
    @PostConstruct
    public void init() {
        try {
            log.info("Initializing ONNX Runtime...");
            
            // Load scaler parameters first
            loadScalerParameters();
            
            // Create ONNX Runtime environment (thread-safe)
            ortEnvironment = OrtEnvironment.getEnvironment();
            log.info("ONNX Runtime environment initialized");
            
            // Load model from file
            log.info("Loading ONNX model from: {}", modelPath);
            ortSession = createSessionFromPath(modelPath);
            log.info("✓ ONNX model loaded successfully");
            
            // Log model metadata for debugging
            logModelMetadata();
            
        } catch (OrtException | IOException e) {
            log.error("Failed to initialize ONNX model service", e);
            throw new RuntimeException("ONNX model initialization failed: " + e.getMessage(), e);
        }
    }
    
    /**
     * Load StandardScaler parameters from JSON configuration file
     */
    private void loadScalerParameters() {
        try {
            ClassPathResource resource = new ClassPathResource("models/scaler_params.json");
            ObjectMapper mapper = new ObjectMapper();
            
            @SuppressWarnings("unchecked")
            Map<String, Object> params = mapper.readValue(resource.getInputStream(), Map.class);
            
            @SuppressWarnings("unchecked")
            List<Double> meanList = (List<Double>) params.get("mean");
            @SuppressWarnings("unchecked")
            List<Double> scaleList = (List<Double>) params.get("scale");
            
            scalerMean = meanList.stream().mapToDouble(Double::doubleValue).toArray();
            scalerScale = scaleList.stream().mapToDouble(Double::doubleValue).toArray();
            nFeatures = ((Number) params.get("n_features")).intValue();
            
            log.info("✓ Scaler parameters loaded: {} features", nFeatures);
            log.debug("  Mean[0]: {}", scalerMean[0]);
            log.debug("  Scale[0]: {}", scalerScale[0]);
            
        } catch (IOException e) {
           log.warn("Failed to load scaler parameters: {}", e.getMessage());
            log.warn("Proceeding without feature normalization (may affect accuracy)");
        }
    }
    
    /**
     * Scale features using StandardScaler parameters (transform: (x - mean) / scale)
     */
    private float[] scaleFeatures(float[] rawFeatures) {
        if (scalerMean == null || scalerScale == null) {
            log.warn("Scaler not initialized, returning raw features");
            return rawFeatures;
        }
        
        float[] scaledFeatures = new float[rawFeatures.length];
        for (int i = 0; i < rawFeatures.length; i++) {
            scaledFeatures[i] = (float) ((rawFeatures[i] - scalerMean[i]) / scalerScale[i]);
        }
        return scaledFeatures;
    }
    
    /**
     * Run inference on extracted features
     * 
     * @param features Array of 22 float values (comprehensive URL features)
     * @return Risk score (probability of phishing) as double between 0 and 1
     * @throws OrtException if inference fails
     */
    public double predict(float[] features) throws OrtException {
        if (features == null || features.length != 22) {
            throw new IllegalArgumentException("Expected 22 features, got " + 
                (features == null ? 0 : features.length));
        }
        
        try {
            // Apply StandardScaler normalization: (x - mean) / scale
            float[] scaledFeatures = scaleFeatures(features);
            
            // Create input tensor: shape [1, 22] for batch size 1, 22 features
            float[][] inputArray = new float[1][22];
            System.arraycopy(scaledFeatures, 0, inputArray[0], 0, 22);
            
            OnnxTensor inputTensor = OnnxTensor.createTensor(ortEnvironment, inputArray);
            
            // Prepare input map with input name "float_input"
            Map<String, OnnxTensor> inputs = new HashMap<>();
            inputs.put("float_input", inputTensor);
            
            // Run inference with 22-feature model
            try (var outputs = ortSession.run(inputs)) {
                double phishingProbability = extractPhishingProbability(outputs);
                log.debug("22-Feature Model Inference - Risk Score: {}", phishingProbability);
                return phishingProbability;
            }
            
        } catch (OrtException e) {
            log.error("ONNX inference failed for features: {}", features, e);
            throw e;
        }
    }
    
    /**
     * Log ONNX model metadata for verification
     */
    private void logModelMetadata() {
        try {
            log.info("=== ONNX Model Metadata ===");
            log.info("Input names: {}", ortSession.getInputNames());
            log.info("Output names: {}", ortSession.getOutputNames());
            
            log.info("Input info: {}", ortSession.getInputInfo().keySet());
            log.info("Output info: {}", ortSession.getOutputInfo().keySet());
        } catch (OrtException e) {
            log.warn("Could not log full model metadata: {}", e.getMessage());
        }
    }

    private double extractPhishingProbability(OrtSession.Result outputs) throws OrtException {
        if (outputs == null || outputs.size() == 0) {
            throw new OrtException("ONNX outputs are empty");
        }

        // ONNX XGBoost classifier outputs:
        // - "label": int64[batch] - classification result  
        // - "probabilities": float32[batch, 2] - [prob_class_0, prob_class_1]
        // We want prob_class_1 (phishing probability)
        
        try {
            // Try to get "probabilities" output by name first
            Object probOutput = outputs.get("probabilities");
            if (probOutput != null) {
                try {
                    Double prob = tryExtractProbability(probOutput);
                    if (prob != null) {
                        log.debug("✓ Extracted phishing probability from 'probabilities' output: {}", prob);
                        return prob;
                    }
                } catch (OrtException e) {
                    log.warn("Could not access 'probabilities' by name: {}", e.getMessage());
                }
            }
        } catch (Exception e) {
            log.warn("Error accessing 'probabilities': {}", e.getMessage());
        }

        // Fallback: iterate through outputs and find float array/matrix
        for (var output : outputs) {
            Object value = output.getValue();
            if (log.isDebugEnabled()) {
                log.debug("ONNX output type: {}", value == null ? "null" : value.getClass().getName());
            }
            
            // Skip integer outputs (classification label)
            if (value instanceof long[] || value instanceof int[]) {
                log.debug("Skipping integer classification output");
                continue;
            }
            
            try {
                Double probability = tryExtractProbability(value);
                if (probability != null) {
                    log.debug("✓ Extracted phishing probability from fallback: {}", probability);
                    return probability;
                }
            } catch (OrtException e) {
                log.warn("Error extracting probability: {}", e.getMessage());
                continue;
            }
        }

        throw new OrtException("Unable to extract phishing probability from ONNX outputs");
    }

    private Double tryExtractProbability(Object value) throws OrtException {
        if (value instanceof OnnxTensor tensor) {
            return tryExtractProbability(tensor.getValue());
        }

        if (value instanceof OnnxSequence sequence) {
            return tryExtractProbability(sequence.getValue());
        }

        if (value instanceof OnnxMap onnxMap) {
            return getProbabilityFromMap(onnxMap.getValue());
        }

        if (value instanceof float[][] floatMatrix && floatMatrix.length > 0 && floatMatrix[0].length > 1) {
            return (double) floatMatrix[0][1];
        }

        if (value instanceof float[] floatArray && floatArray.length > 1) {
            return (double) floatArray[1];
        }

        if (value instanceof Map<?, ?> mapValue) {
            return getProbabilityFromMap(mapValue);
        }

        if (value instanceof Map<?, ?>[] mapArray && mapArray.length > 0) {
            return getProbabilityFromMap(mapArray[0]);
        }

        if (value instanceof List<?> listValue && !listValue.isEmpty()) {
            try {
                Object first = listValue.get(0);
                if (first instanceof OnnxMap onnxMap) {
                    return getProbabilityFromMap(onnxMap.getValue());
                }
                if (first instanceof Map<?, ?> map) {
                    return getProbabilityFromMap(map);
                }
                if (first instanceof OnnxTensor tensor) {
                    return tryExtractProbability(tensor.getValue());
                }
            } catch (OrtException e) {
                log.warn("Failed to read ONNX list value: {}", e.getMessage());
                return null;
            }
        }

        return null;
    }

    private Double getProbabilityFromMap(Map<?, ?> mapValue) {
        if (mapValue.containsKey(1L)) {
            return ((Number) mapValue.get(1L)).doubleValue();
        }
        if (mapValue.containsKey(1)) {
            return ((Number) mapValue.get(1)).doubleValue();
        }
        return null;
    }

    private OrtSession createSessionFromPath(String path) throws OrtException, IOException {
        OrtSession.SessionOptions options = new OrtSession.SessionOptions();
        if (path != null && path.startsWith("classpath:")) {
            String resourcePath = path.substring("classpath:".length());
            if (resourcePath.startsWith("/")) {
                resourcePath = resourcePath.substring(1);
            }
            @SuppressWarnings("null")
            ClassPathResource resource = new ClassPathResource(resourcePath);
            if (!resource.exists()) {
                throw new FileNotFoundException("ONNX model not found at classpath:" + resourcePath);
            }
            try (InputStream inputStream = resource.getInputStream()) {
                byte[] modelBytes = inputStream.readAllBytes();
                return ortEnvironment.createSession(modelBytes, options);
            }
        }

        return ortEnvironment.createSession(path, options);
    }
    
    /**
     * Check if model is ready for inference
     * 
     * @return true if model loaded successfully
     */
    public boolean isReady() {
        return ortSession != null;
    }
    
    /**
     * Cleanup resources
     */
    public void shutdown() {
        try {
            if (ortSession != null) {
                ortSession.close();
                log.info("ONNX session closed");
            }
            if (ortEnvironment != null) {
                ortEnvironment.close();
                log.info("ONNX environment closed");
            }
        } catch (OrtException e) {
            log.warn("Error during ONNX cleanup: {}", e.getMessage());
        }
    }
}
