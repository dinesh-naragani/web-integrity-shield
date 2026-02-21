package com.wsi.phishing.service;

import java.time.Duration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import com.wsi.phishing.dto.DeepAnalyzeRequest;
import com.wsi.phishing.dto.DeepAnalyzeResponse;


/**
 * Level-2 Deep Analysis Service
 * 
 * Communicates with Python Level-2 microservice running on localhost:8001
 * 
 * Responsibilities:
 * - Call /deep-analyze endpoint
 * - Handle timeout and errors gracefully
 * - Fallback to Level-1 result if Level-2 fails
 */
@Service
public class Level2Service {

    private static final Logger log = LoggerFactory.getLogger(Level2Service.class);
    
    private static final String LEVEL2_SERVICE_URL = "http://localhost:8001";
    private static final String DEEP_ANALYZE_ENDPOINT = "/deep-analyze";
    private static final int TIMEOUT_SECONDS = 12;

    @Autowired
    private WebClient webClient;

    /**
     * Call Level-2 deep analysis service
     * 
     * @param url URL to analyze
     * @param riskScore Level-1 risk score
     * @return DeepAnalyzeResponse with Level-2 analysis, or null if fails
     */
    public DeepAnalyzeResponse analyze(String url, double riskScore) {
        long startTime = System.currentTimeMillis();
        boolean fallback = false;
        DeepAnalyzeResponse response;
        try {
            if (url == null || url.trim().isEmpty()) {
                log.warn("Level-2: Invalid URL provided");
                fallback = true;
                return null;
            }

            log.info("Level-2: Calling deep analysis service for URL: {}", maskUrl(url));
            
            DeepAnalyzeRequest request = new DeepAnalyzeRequest(url, riskScore);
            
            // Build URL for Level-2 service
            String serviceUrl = LEVEL2_SERVICE_URL + DEEP_ANALYZE_ENDPOINT;
            
            // Call Level-2 service with timeout protection
            response = webClient
                .post()
                .uri(serviceUrl)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(DeepAnalyzeResponse.class)
                .timeout(Duration.ofSeconds(TIMEOUT_SECONDS))
                .block();  // Synchronous call as per requirements
            
            if (response == null) {
                log.warn("Level-2: Received null response from service");
                fallback = true;
                return null;
            }
            
            if (!response.isValid()) {
                log.warn("Level-2: Invalid response structure: {}", response);
                fallback = true;
                return null;
            }
            
            log.info("Level-2: Analysis complete - Score: {:.3f}, Verdict: {}, AnalysisId: {}",
                response.getLevel2Score(), response.getFinalVerdict(), response.getAnalysisId());
            
            return response;
            
        } catch (WebClientResponseException.ServiceUnavailable e) {
            log.warn("Level-2: Service unavailable (500/503): {}", e.getStatusCode());
            fallback = true;
            return null;
        } catch (WebClientResponseException.BadRequest e) {
            // SSRF or invalid URL blocked by Level-2
            log.warn("Level-2: Bad request (400) - likely SSRF block: {}", e.getResponseBodyAsString());
            fallback = true;
            return null;
        } catch (WebClientResponseException e) {
            log.warn("Level-2: HTTP error {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            fallback = true;
            return null;
        } catch (io.netty.handler.timeout.ReadTimeoutException e) {
            log.warn("Level-2: Timeout after {} seconds: {}", TIMEOUT_SECONDS, e.getMessage());
            fallback = true;
            return null;
        } catch (Exception e) {
            log.error("Level-2: Unexpected error calling service: {}", e.getMessage(), e);
            fallback = true;
            return null;
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("Level-2 call completed in {} ms", duration);
            if (fallback) {
                log.warn("Level-2 fallback triggered after {} ms", duration);
            }
        }
    }

    /**
     * Check if Level-2 service is accessible
     * 
     * @return true if service is reachable
     */
    public boolean isAvailable() {
        try {
            String healthUrl = LEVEL2_SERVICE_URL + "/health";
            
            String response = webClient
                .get()
                .uri(healthUrl)
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofSeconds(3))
                .block();
            
            return response != null;
        } catch (Exception e) {
            log.debug("Level-2: Service not available: {}", e.getMessage());
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
}
