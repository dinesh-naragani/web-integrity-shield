package com.wsi.phishing.controller;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.wsi.phishing.dto.DeepAnalyzeResponse;
import com.wsi.phishing.dto.UrlRequest;
import com.wsi.phishing.dto.UrlResponse;
import com.wsi.phishing.service.Level2Service;
import com.wsi.phishing.service.OnnxModelService;
import com.wsi.phishing.util.FeatureExtractor;


/**
 * REST Controller for URL Phishing Check
 * 
 * Endpoint: POST /check-url
 * Input: { "url": "https://example.com" }
 * Output: { "riskScore": 0.87, "level1Label": "PHISHING", "triggerLevel2": true }
 */
@RestController
@RequestMapping("/")
public class UrlController {

    private static final Logger log = LoggerFactory.getLogger(UrlController.class);
    
    // Risk threshold for triggering Level-2 deep analysis
    private static final double LEVEL2_THRESHOLD = 0.7;
    
    @Autowired
    private OnnxModelService onnxModelService;
    
    @Autowired
    private Level2Service level2Service;
    
    /**
     * Check URL for phishing characteristics at Level-1
     * 
     * @param request UrlRequest containing URL to check
     * @return UrlResponse with risk score and decision
     */
    @PostMapping("/check-url")
    public ResponseEntity<?> checkUrl(@RequestBody UrlRequest request) {
        try {
            // Validate request
            if (request == null || !request.isValid()) {
                log.warn("Invalid request: URL is missing or empty");
                return ResponseEntity
                    .status(HttpStatus.BAD_REQUEST)
                    .body(new ErrorResponse("Invalid request: URL is required"));
            }
            
            String url = request.getUrl();
            log.info("Checking URL: {}", maskUrl(url));
            
            // Validate that it's a proper URL format
            if (!isValidUrl(url)) {
                log.warn("Invalid URL format: {}", maskUrl(url));
                return ResponseEntity
                    .status(HttpStatus.BAD_REQUEST)
                    .body(new ErrorResponse("Invalid URL format"));
            }
            
            // Extract features (deterministic)
            log.debug("Extracting features from URL");
            float[] features = FeatureExtractor.extractFeatures(url);
            
            // Validate features
            if (!FeatureExtractor.validateFeatures(features)) {
                log.error("Feature validation failed for URL: {}", maskUrl(url));
                return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse("Feature extraction validation failed"));
            }
            
            log.debug("Features extracted successfully");
            
            // Run ONNX inference
            double riskScore = onnxModelService.predict(features);
            
            // Determine label based on risk score
            String level1Label = riskScore >= 0.5 ? "PHISHING" : "LEGITIMATE";
            
            // Determine if Level-2 deep analysis should be triggered
            boolean triggerLevel2 = riskScore >= LEVEL2_THRESHOLD;
            
            log.info("Level-1 Result - URL: {}, Risk: {:.4f}, Label: {}, TriggerL2: {}",
                maskUrl(url), riskScore, level1Label, triggerLevel2);
            
            // Build response with Level-1 data
            UrlResponse response = UrlResponse.builder()
                .url(url)
                .riskScore(riskScore)
                .level1Label(level1Label)
                .triggerLevel2(triggerLevel2)
                .level2Status(triggerLevel2 ? "FALLBACK" : "NOT_TRIGGERED")
                .finalVerdict(level1Label)  // Default to Level-1 label
                .reasons(new ArrayList<>())
                .build();
            
            // Call Level-2 service if threshold triggered
            if (triggerLevel2) {
                log.debug("Level-2 threshold triggered, calling Level-2 service...");
                DeepAnalyzeResponse level2Response = level2Service.analyze(url, riskScore);
                
                if (level2Response != null && level2Response.isValid()) {
                    // Level-2 analysis successful - merge into response
                    response.setLevel2Status("SUCCESS");
                    response.setAnalysisId(level2Response.getAnalysisId());
                    response.setLevel2Score(level2Response.getLevel2Score());
                    response.setFinalVerdict(level2Response.getFinalVerdict());
                    response.setReasons(level2Response.getReasons() != null ? 
                        level2Response.getReasons() : new ArrayList<>());
                    
                    log.info("Level-2 Result Merged - AnalysisId: {}, L2Score: {:.3f}, Verdict: {}",
                        level2Response.getAnalysisId(), level2Response.getLevel2Score(), 
                        level2Response.getFinalVerdict());
                } else {
                    // Level-2 failed - fallback to Level-1
                    log.warn("Level-2 analysis failed or unavailable - using Level-1 result");
                    response.setLevel2Status("FALLBACK");
                    response.setAnalysisId(null);
                    response.setLevel2Score(null);
                    response.setFinalVerdict(level1Label);
                    response.setReasons(new ArrayList<>());
                }
            }
            
            return ResponseEntity.ok(response);
            
        } catch (ai.onnxruntime.OrtException e) {
            log.error("ONNX inference failed", e);
            return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ErrorResponse("Inference failed: " + e.getMessage()));
        } catch (RuntimeException e) {
            log.error("Inference failed", e);
            return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ErrorResponse("Inference failed: " + e.getMessage()));
        }
    }
    
    /**
     * Validate URL format
     * 
     * @param urlString URL to validate
     * @return true if valid URL format
     */
    private boolean isValidUrl(String urlString) {
        try {
            URI uri = new URI(urlString);
            return uri.getScheme() != null && uri.getHost() != null;
        } catch (URISyntaxException e) {
            return false;
        }
    }
    
    /**
     * Mask URL for logging (hide sensitive parts)
     * 
     * @param url URL to mask
     * @return Masked URL
     */
    private String maskUrl(String url) {
        if (url == null || url.length() < 20) {
            return url;
        }
        return url.substring(0, 10) + "..." + url.substring(url.length() - 10);
    }
    
    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<?> health() {
        if (onnxModelService.isReady()) {
            return ResponseEntity.ok(new HealthResponse("OK", "ONNX model is ready"));
        } else {
            return ResponseEntity
                .status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(new HealthResponse("UNAVAILABLE", "ONNX model not loaded"));
        }
    }
    
    // Helper classes for responses
    
    public static class ErrorResponse {
        public String error;
        
        public ErrorResponse(String error) {
            this.error = error;
        }
        
        public String getError() {
            return error;
        }
    }
    
    public static class HealthResponse {
        public String status;
        public String message;
        
        public HealthResponse(String status, String message) {
            this.status = status;
            this.message = message;
        }
        
        public String getStatus() {
            return status;
        }
        
        public String getMessage() {
            return message;
        }
    }
}
