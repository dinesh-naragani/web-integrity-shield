package com.wsi.phishing;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

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
        log.info("Starting Web Integrity Shield Backend v2.0.0...");
        SpringApplication.run(WebIntegrityShieldApplication.class, args);
        log.info("Web Integrity Shield Backend started successfully");
        log.info("Server ready on http://localhost:8080");
    }
}
