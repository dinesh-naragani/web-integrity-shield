package com.wsi.phishing;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Web Integrity Shield Backend Application
 * 
 * Level-1 Phishing Detection using ONNX Runtime
 * 
 * Main class for Spring Boot application startup
 */
@SpringBootApplication
public class WebIntegrityShieldApplication {

    private static final Logger log = LoggerFactory.getLogger(WebIntegrityShieldApplication.class);

    public static void main(String[] args) {
        log.info("Starting Web Integrity Shield Backend...");
        SpringApplication.run(WebIntegrityShieldApplication.class, args);
        log.info("✓ Application started successfully");
        log.info("POST /check-url endpoint ready for requests");
        log.info("GET /health endpoint available for health checks");
    }
}
