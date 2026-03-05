package com.wsi.phishing.service;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wsi.phishing.util.ComprehensiveFeatureExtractor;

import ai.onnxruntime.OrtException;
import jakarta.annotation.PostConstruct;

@Service
public class HybridDetectionService {

    private static final Logger log = LoggerFactory.getLogger(HybridDetectionService.class);

    private static final Set<String> SUSPICIOUS_TLDS = Set.of(
        "tk", "ga", "ml", "cf", "gq",
        "top", "loan", "download", "science", "stream",
        "re", "men", "works", "phone", "webcam"
    );

    private static final Set<String> BRAND_NAMES = Set.of(
        "paypal", "amazon", "apple", "google", "facebook", "microsoft", "netflix",
        "ebay", "linkedin", "twitter", "instagram", "youtube", "github"
    );

    private static final List<Pattern> SUSPICIOUS_PATTERNS = List.of(
        Pattern.compile("verify|confirm|secure|update|alert|validate|authenticate", Pattern.CASE_INSENSITIVE),
        Pattern.compile("login|signin|account|password|credentials|reset|recovery", Pattern.CASE_INSENSITIVE),
        Pattern.compile("click|urgent|action|required|expired|confirm", Pattern.CASE_INSENSITIVE),
        Pattern.compile("payment|billing|subscription|refund|claim|prize", Pattern.CASE_INSENSITIVE)
    );

    private final OnnxModelService onnxModelService;
    private final ObjectMapper objectMapper;

    private Set<String> domainWhitelist = new HashSet<>();

    public HybridDetectionService(OnnxModelService onnxModelService, ObjectMapper objectMapper) {
        this.onnxModelService = onnxModelService;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    public void init() {
        loadDomainWhitelist();
    }

    public HybridDetectionResult detect(String url) throws OrtException {
        String domain = extractDomain(url);
        String host = extractHost(url);
        String tld = getTld(domain);

        if (isWhitelisted(domain)) {
            return new HybridDetectionResult("LEGITIMATE", 0.99, "Known legitimate domain");
        }

        String parentDomain = getParentDomain(domain);
        if (parentDomain != null && isWhitelisted(parentDomain)) {
            return new HybridDetectionResult("LEGITIMATE", 0.95, "Known legitimate parent domain");
        }

        String hostWithoutPort = host.contains(":") ? host.split(":", 2)[0] : host;
        if (isIpAddress(hostWithoutPort)) {
            return new HybridDetectionResult("PHISHING", 0.95, "IP-based URL (suspicious)");
        }

        if (SUSPICIOUS_TLDS.contains(tld)) {
            return new HybridDetectionResult("PHISHING", 0.90, "Suspicious TLD: ." + tld);
        }

        if (isTyposquatting(domain)) {
            return new HybridDetectionResult("PHISHING", 0.85, "Possible typosquatting (similar to known brand)");
        }

        if (hasSuspiciousPattern(url)) {
            return new HybridDetectionResult("PHISHING", 0.75, "Suspicious URL pattern");
        }

        float[] features = ComprehensiveFeatureExtractor.extractComprehensiveFeatures(url);
        if (!ComprehensiveFeatureExtractor.validateFeatures(features)) {
            throw new RuntimeException("Feature extraction validation failed");
        }

        double modelRisk = onnxModelService.predict(features);
        if (modelRisk > 0.9 || modelRisk < 0.1) {
            String verdict = modelRisk >= 0.5 ? "PHISHING" : "LEGITIMATE";
            return new HybridDetectionResult(verdict, modelRisk,
                String.format(Locale.ROOT, "ML model prediction (confidence: %.2f)", modelRisk));
        }

        return new HybridDetectionResult("LEGITIMATE", 0.50, "No suspicious patterns detected");
    }

    private void loadDomainWhitelist() {
        try {
            ClassPathResource resource = new ClassPathResource("models/domain_whitelist.json");
            if (!resource.exists()) {
                log.warn("domain_whitelist.json not found, whitelist checks disabled");
                return;
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> payload = objectMapper.readValue(resource.getInputStream(), Map.class);
            Object rawWhitelist = payload.get("whitelist");
            if (rawWhitelist instanceof List<?> entries) {
                domainWhitelist = entries.stream()
                    .filter(String.class::isInstance)
                    .map(String.class::cast)
                    .map(v -> v.toLowerCase(Locale.ROOT))
                    .collect(java.util.stream.Collectors.toSet());
            }

            log.info("Loaded {} whitelisted domains", domainWhitelist.size());
        } catch (IOException e) {
            log.warn("Failed to load domain whitelist: {}", e.getMessage());
        }
    }

    private boolean isWhitelisted(String domain) {
        return domain != null && !domain.isBlank() && domainWhitelist.contains(domain.toLowerCase(Locale.ROOT));
    }

    private String extractHost(String url) {
        try {
            URI uri = new URI(url);
            return uri.getHost() == null ? "" : uri.getHost().toLowerCase(Locale.ROOT);
        } catch (URISyntaxException e) {
            return "";
        }
    }

    private String extractDomain(String url) {
        String host = extractHost(url);
        if (host.startsWith("www.")) {
            return host.substring(4);
        }
        return host;
    }

    private String getParentDomain(String domain) {
        if (domain == null || domain.isBlank()) {
            return null;
        }
        String[] parts = domain.split("\\.");
        if (parts.length <= 2) {
            return null;
        }
        return String.join(".", Arrays.copyOfRange(parts, parts.length - 2, parts.length));
    }

    private String getTld(String domain) {
        if (domain == null || domain.isBlank()) {
            return "";
        }
        String[] parts = domain.split("\\.");
        if (parts.length < 2) {
            return "";
        }
        if (parts.length >= 3 && "co".equals(parts[parts.length - 2])) {
            return parts[parts.length - 2] + "." + parts[parts.length - 1];
        }
        return parts[parts.length - 1];
    }

    private boolean isIpAddress(String host) {
        if (host == null || host.isBlank()) {
            return false;
        }
        return host.matches("^(\\d{1,3}\\.){3}\\d{1,3}$");
    }

    private boolean isTyposquatting(String domain) {
        if (domain == null || domain.isBlank()) {
            return false;
        }

        String mainPart = domain.split("\\.")[0].toLowerCase(Locale.ROOT);
        int minDistance = Integer.MAX_VALUE;

        for (String brand : BRAND_NAMES) {
            int distance = levenshteinDistance(mainPart, brand);
            minDistance = Math.min(minDistance, distance);
        }

        return minDistance <= 2;
    }

    private int levenshteinDistance(String left, String right) {
        if (left.length() < right.length()) {
            return levenshteinDistance(right, left);
        }
        if (right.isEmpty()) {
            return left.length();
        }

        int[] previous = new int[right.length() + 1];
        for (int i = 0; i <= right.length(); i++) {
            previous[i] = i;
        }

        for (int i = 0; i < left.length(); i++) {
            int[] current = new int[right.length() + 1];
            current[0] = i + 1;
            for (int j = 0; j < right.length(); j++) {
                int insertions = previous[j + 1] + 1;
                int deletions = current[j] + 1;
                int substitutions = previous[j] + (left.charAt(i) == right.charAt(j) ? 0 : 1);
                current[j + 1] = Math.min(Math.min(insertions, deletions), substitutions);
            }
            previous = current;
        }

        return previous[right.length()];
    }

    private boolean hasSuspiciousPattern(String url) {
        for (Pattern pattern : SUSPICIOUS_PATTERNS) {
            if (pattern.matcher(url).find()) {
                return true;
            }
        }
        return false;
    }

    public record HybridDetectionResult(String verdict, double riskScore, String reason) {}
}