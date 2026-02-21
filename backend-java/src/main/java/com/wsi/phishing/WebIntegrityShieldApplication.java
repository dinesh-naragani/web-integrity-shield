package com.wsi.phishing;

import com.wsi.phishing.service.Level2Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

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
    }

    @Bean
    public ApplicationRunner startupLogger(Level2Service level2Service) {
        return args -> {
            log.info("Web Integrity Shield Backend v2.0.0 started successfully");
            log.info("Level-2 service availability: {}", level2Service.isAvailable());
        };
    }
}
