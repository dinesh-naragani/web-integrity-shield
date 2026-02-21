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
 * Loads Random Forest model at application startup.
 * Provides synchronous inference on URL features.
 * 
 * Model: url_model.onnx
 * - Input: float[1, 7] (7 URL features)
 * - Output: float[1, 2] (probability distribution for 2 classes)
 *   Index 1: Probability of phishing (class 1)
 */
@Service
public class OnnxModelService {

    private static final Logger log = LoggerFactory.getLogger(OnnxModelService.class);
    
    @Value("${onnx.model.path:classpath:models/url_model.onnx}")
    private String modelPath;
    
    private OrtEnvironment ortEnvironment;
    private OrtSession ortSession;
    
    /**
     * Initialize ONNX Runtime environment and load model at startup
     */
    @PostConstruct
    public void init() {
        try {
            log.info("Initializing ONNX Runtime...");
            
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
     * Run inference on extracted features
     * 
     * @param features Array of 7 float values (URL features)
     * @return Risk score (probability of phishing) as double between 0 and 1
     * @throws OrtException if inference fails
     */
    public double predict(float[] features) throws OrtException {
        if (features == null || features.length != 7) {
            throw new IllegalArgumentException("Expected 7 features, got " + 
                (features == null ? 0 : features.length));
        }
        
        try {
            // Create input tensor: shape [1, 7] for batch size 1, 7 features
            float[][] inputArray = new float[1][7];
            System.arraycopy(features, 0, inputArray[0], 0, 7);
            
            OnnxTensor inputTensor = OnnxTensor.createTensor(ortEnvironment, inputArray);
            
            // Prepare input map with input name "float_input"
            // Note: Check ONNX model metadata for actual input/output names
            Map<String, OnnxTensor> inputs = new HashMap<>();
            inputs.put("float_input", inputTensor);
            
            // Run inference
            try (var outputs = ortSession.run(inputs)) {
                double phishingProbability = extractPhishingProbability(outputs);
                log.debug("Inference result - Phishing probability: {}", phishingProbability);
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

        for (var output : outputs) {
            Object value = output.getValue();
            if (log.isDebugEnabled()) {
                log.debug("ONNX output type: {}", value == null ? "null" : value.getClass().getName());
                log.debug("ONNX output value: {}", value);
            }
            Double probability = tryExtractProbability(value);
            if (probability != null) {
                return probability;
            }
        }

        throw new OrtException("Unable to extract phishing probability from ONNX outputs");
    }

    private Double tryExtractProbability(Object value) {
        try {
            if (value instanceof OnnxTensor tensor) {
                return tryExtractProbability(tensor.getValue());
            }

            if (value instanceof OnnxSequence sequence) {
                return tryExtractProbability(sequence.getValue());
            }

            if (value instanceof OnnxMap onnxMap) {
                return getProbabilityFromMap(onnxMap.getValue());
            }
        } catch (OrtException e) {
            log.warn("Failed to read ONNX output value: {}", e.getMessage());
            return null;
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
            Object first = listValue.get(0);
            if (first instanceof OnnxMap onnxMap) {
                try {
                    return getProbabilityFromMap(onnxMap.getValue());
                } catch (OrtException e) {
                    log.warn("Failed to read ONNX map value: {}", e.getMessage());
                    return null;
                }
            }
            if (first instanceof Map<?, ?> map) {
                return getProbabilityFromMap(map);
            }
            if (first instanceof OnnxTensor tensor) {
                try {
                    return tryExtractProbability(tensor.getValue());
                } catch (OrtException e) {
                    log.warn("Failed to read ONNX tensor value: {}", e.getMessage());
                    return null;
                }
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
