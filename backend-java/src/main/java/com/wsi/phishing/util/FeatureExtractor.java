package com.wsi.phishing.util;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Feature Extractor for Phishing URLs - Java Implementation
 * 
 * Extracts 7 deterministic URL features in fixed order.
 * Must match Python implementation exactly for model consistency.
 * 
 * Features (in order):
 * 1. url_length - Length of the URL
 * 2. dot_count - Number of dots in URL
 * 3. hyphen_count - Number of hyphens in URL
 * 4. special_char_count - Number of special characters
 * 5. has_https - Binary: 1.0 if HTTPS, 0.0 otherwise
 * 6. has_ip - Binary: 1.0 if IP address detected, 0.0 otherwise
 * 7. suspicious_keyword_count - Count of suspicious keywords
 */
public class FeatureExtractor {
    
    // Suspicious keywords for phishing detection
    private static final Set<String> SUSPICIOUS_KEYWORDS = new HashSet<>(Arrays.asList(
        "phish", "login", "signin", "verify", "update", "confirm", "account", 
        "secure", "banking", "paypal", "amazon", "apple", "microsoft", "fake", 
        "clone", "bit.ly", "tinyurl", "short", "click", "urgent", "alert", 
        "suspend", "activity", "unusual"
    ));
    
    // IPv4 pattern: 0-255.0-255.0-255.0-255
    private static final Pattern IPV4_PATTERN = Pattern.compile(
        "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    );
    
    // IPv6 pattern (simplified)
    private static final Pattern IPV6_PATTERN = Pattern.compile(
        "[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}"
    );
    
    // Special characters pattern
    private static final Pattern SPECIAL_CHARS_PATTERN = Pattern.compile(
        "[@#$%&*+=?!~^()\\[\\]{}|\\\\:;\"'<>]"
    );
    
    /**
     * Extract 7 features from URL in deterministic order.
     * 
     * @param url The URL string to analyze
     * @return Array of 7 float values in fixed order
     */
    public static float[] extractFeatures(String url) {
        // Normalize: strip whitespace
        url = url.trim();
        
        // Feature 1: URL Length
        float urlLength = url.length();
        
        // Feature 2: Dot Count
        float dotCount = countOccurrences(url, '.');
        
        // Feature 3: Hyphen Count
        float hyphenCount = countOccurrences(url, '-');
        
        // Feature 4: Special Character Count
        int specialCharCount = 0;
        Matcher specialMatcher = SPECIAL_CHARS_PATTERN.matcher(url);
        while (specialMatcher.find()) {
            specialCharCount++;
        }
        
        // Feature 5: HTTPS Presence (0 or 1)
        float hasHttps = url.startsWith("https://") ? 1.0f : 0.0f;
        
        // Feature 6: IP Address Presence (0 or 1)
        float hasIp = containsIpAddress(url) ? 1.0f : 0.0f;
        
        // Feature 7: Suspicious Keyword Count
        float suspiciousKeywordCount = countSuspiciousKeywords(url);
        
        // Return in fixed order - CRITICAL FOR MODEL INFERENCE
        return new float[]{
            urlLength,           // Feature 1
            dotCount,            // Feature 2
            hyphenCount,         // Feature 3
            specialCharCount,    // Feature 4
            hasHttps,            // Feature 5
            hasIp,               // Feature 6
            suspiciousKeywordCount // Feature 7
        };
    }
    
    /**
     * Get feature names in extraction order
     * 
     * @return List of feature names matching extraction order
     */
    public static List<String> getFeatureNames() {
        return Arrays.asList(
            "url_length",
            "dot_count",
            "hyphen_count",
            "special_char_count",
            "has_https",
            "has_ip",
            "suspicious_keyword_count"
        );
    }
    
    /**
     * Validate extracted features against expected range
     * 
     * @param features Array of 7 feature values
     * @return true if valid, false otherwise
     */
    public static boolean validateFeatures(float[] features) {
        // Must have exactly 7 features
        if (features == null || features.length != 7) {
            return false;
        }
        
        // Binary features (indices 4, 5) must be 0.0 or 1.0
        if (features[4] != 0.0f && features[4] != 1.0f) {
            return false;
        }
        if (features[5] != 0.0f && features[5] != 1.0f) {
            return false;
        }
        
        // All features must be non-negative
        for (float feature : features) {
            if (feature < 0) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Count occurrences of a character in a string
     * 
     * @param str The string to search in
     * @param ch The character to count
     * @return Number of occurrences
     */
    private static int countOccurrences(String str, char ch) {
        int count = 0;
        for (char c : str.toCharArray()) {
            if (c == ch) {
                count++;
            }
        }
        return count;
    }
    
    /**
     * Detect if URL contains an IP address (IPv4 or IPv6)
     * 
     * @param url The URL to check
     * @return true if URL contains IP address, false otherwise
     */
    private static boolean containsIpAddress(String url) {
        // Check IPv4: 0-255.0-255.0-255.0-255
        if (IPV4_PATTERN.matcher(url).find()) {
            return true;
        }
        
        // Check IPv6: simplified detection
        return url.contains("::") || IPV6_PATTERN.matcher(url).find();
    }
    
    /**
     * Count occurrences of suspicious keywords in URL (case-insensitive)
     * 
     * @param url The URL to analyze
     * @return Count of suspicious keyword matches
     */
    private static int countSuspiciousKeywords(String url) {
        String urlLower = url.toLowerCase();
        int count = 0;
        
        for (String keyword : SUSPICIOUS_KEYWORDS) {
            int index = 0;
            while ((index = urlLower.indexOf(keyword, index)) != -1) {
                count++;
                index += keyword.length();
            }
        }
        
        return count;
    }
}
