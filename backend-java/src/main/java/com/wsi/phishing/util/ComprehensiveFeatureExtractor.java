package com.wsi.phishing.util;

import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Comprehensive Feature Extractor - 22 Features
 * 
 * Extracts 22 URL-based features for robust phishing detection.
 * Includes domain intelligence to eliminate false positives.
 * Matches Python comprehensive_feature_extractor.py exactly.
 * 
 * Features:
 * 1. URLLength - Total length of URL
 * 2. DomainLength - Domain name length (without TLD)
 * 3. TLDLength - Top-level domain length
 * 4. IsDomainIP - Is domain an IP address? (1.0/0.0)
 * 5. NoOfSubDomain - Count of subdomains
 * 6. IsHTTPS - Uses HTTPS? (1.0/0.0) [MOST IMPORTANT - 60.71%]
 * 7. NoOfLettersInURL - Alphabetic character count
 * 8. NoOfDigitsInURL - Numeric character count
 * 9. NoOfEqualsInURL - Count of '=' characters
 * 10. NoOfQMarkInURL - Count of '?' characters
 * 11. NoOfAmpersandInURL - Count of '&' characters
 * 12. NoOfOtherSpecialCharsInURL - Count of other special chars
 * 13. LetterRatioInURL - Letters / Total length
 * 14. DigitRatioInURL - Digits / Total length
 * 15. SpecialCharRatioInURL - Special chars / Total length
 * 16. CharContinuationRate - Longest consecutive identical character [30.71%]
 * 17. URLCharProb - Shannon entropy of character distribution
 * 18. DomainHasHyphen - Domain contains hyphen? (1.0/0.0)
 * 19. URLHasDblSlash - Count of '//' occurrences
 * 20. HasObfuscation - Obfuscation detected? (1.0/0.0)
 * 21. TLDIsLegitimate - TLD is known good? (1.0/0.0)
 * 22. DomainIsKnownSafe - Domain in whitelist? (1.0/0.0) [FIXES FALSE POSITIVES]
 */
public class ComprehensiveFeatureExtractor {
    
    // Legitimate TLDs
    private static final Set<String> LEGITIMATE_TLDS = new HashSet<>(Arrays.asList(
        "com", "org", "net", "edu", "gov", "co", "uk", "de", "fr",
        "it", "es", "nl", "be", "ch", "at", "se", "no", "dk", "fi",
        "io", "ai", "dev", "app", "tech", "cloud", "digital"
    ));
    
    // Known safe domains whitelist
    private static final Set<String> KNOWN_SAFE_DOMAINS = new HashSet<>(Arrays.asList(
        "google.com", "facebook.com", "microsoft.com", "apple.com", "amazon.com",
        "youtube.com", "gmail.com", "github.com", "stackoverflow.com", "wikipedia.org",
        "discord.com", "slack.com", "telegram.org", "twitter.com", "reddit.com",
        "chatgpt.com", "openai.com", "claude.ai", "netflix.com", "linkedin.com",
        "instagram.com", "twitch.tv", "paypal.com", "stripe.com", "heroku.com",
        "aws.amazon.com", "cloud.google.com", "azure.microsoft.com",
        "example.com", "www.example.com"
    ));
    
    // IPv4 pattern
    private static final Pattern IPV4_PATTERN = Pattern.compile(
        "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    );
    
    // IPv6 pattern
    private static final Pattern IPV6_PATTERN = Pattern.compile(
        "[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}"
    );
    
    /**
     * Extract 22 comprehensive features from URL
     * 
     * @param url The URL string to analyze
     * @return Array of 22 float values in fixed order
     */
    public static float[] extractComprehensiveFeatures(String url) {
        url = url.trim();
        
        // Parse URL to extract domain and TLD
        String domain = extractDomain(url);
        String domainClean = domain.startsWith("www.") ? domain.substring(4) : domain;
        String[] domainParts = domainClean.split("\\.");
        String tld = domainParts.length > 0 ? domainParts[domainParts.length - 1] : "";
        
        // Feature 1: URL Length
        float urlLength = (float) url.length();
        
        // Feature 2: Domain Length (without TLD)
        float domainLength = 0;
        if (domainParts.length >= 2) {
            String domainName = String.join(".", Arrays.copyOfRange(domainParts, 0, domainParts.length - 1));
            domainLength = (float) domainName.length();
        } else {
            domainLength = (float) domainClean.length();
        }
        
        // Feature 3: TLD Length
        float tldLength = (float) tld.length();
        
        // Feature 4: Is Domain IP?
        float isDomainIP = isIpAddress(domain) ? 1.0f : 0.0f;
        
        // Feature 5: Number of Subdomains
        float numSubdomains = (float) Math.max(0, domain.split("\\.").length - 1);
        
        // Feature 6: Is HTTPS?
        float isHttps = url.startsWith("https://") ? 1.0f : 0.0f;
        
        // Feature 7: Number of Letters
        float numLetters = countCharType(url, c -> Character.isLetter(c));
        
        // Feature 8: Number of Digits
        float numDigits = countCharType(url, c -> Character.isDigit(c));
        
        // Feature 9: Number of '='
        float numEquals = countOccurrence(url, '=');
        
        // Feature 10: Number of '?'
        float numQMark = countOccurrence(url, '?');
        
        // Feature 11: Number of '&'
        float numAmpersand = countOccurrence(url, '&');
        
        // Feature 12: Number of Other Special Chars
        float numOtherSpecial = countOtherSpecialChars(url);
        
        // Feature 13: Letter Ratio
        float letterRatio = urlLength > 0 ? numLetters / urlLength : 0.0f;
        
        // Feature 14: Digit Ratio
        float digitRatio = urlLength > 0 ? numDigits / urlLength : 0.0f;
        
        // Feature 15: Special Character Ratio
        float numSpecial = countSpecialChars(url);
        float specialRatio = urlLength > 0 ? numSpecial / urlLength : 0.0f;
        
        // Feature 16: Character Continuation Rate
        float charContinuation = (float) getMaxConsecutiveChar(url);
        
        // Feature 17: URL Character Probability (Shannon Entropy)
        float entropy = calculateEntropy(url);
        
        // Feature 18: Domain Has Hyphen?
        float domainHasHyphen = domainClean.contains("-") ? 1.0f : 0.0f;
        
        // Feature 19: URL Has Double Slash Count
        float dblSlashCount = countOccurrence(url, '/') / 2.0f;  // Count pairs
        if (url.contains("//")) {
            dblSlashCount = (float) countDblSlash(url);
        }
        
        // Feature 20: Has Obfuscation?
        float hasObfuscation = detectObfuscation(url) ? 1.0f : 0.0f;
        
        // Feature 21: TLD Is Legitimate?
        float tldIsLegit = LEGITIMATE_TLDS.contains(tld.toLowerCase()) ? 1.0f : 0.0f;
        
        // Feature 22: Domain Is Known Safe?
        float domainIsSafe = isKnownSafeDomain(domainClean) ? 1.0f : 0.0f;
        
        // Return in fixed order - CRITICAL FOR MODEL INFERENCE
        return new float[]{
            urlLength,                  // 1
            domainLength,               // 2
            tldLength,                  // 3
            isDomainIP,                 // 4
            numSubdomains,              // 5
            isHttps,                    // 6
            numLetters,                 // 7
            numDigits,                  // 8
            numEquals,                  // 9
            numQMark,                   // 10
            numAmpersand,               // 11
            numOtherSpecial,            // 12
            letterRatio,                // 13
            digitRatio,                 // 14
            specialRatio,               // 15
            charContinuation,           // 16
            entropy,                    // 17
            domainHasHyphen,            // 18
            dblSlashCount,              // 19
            hasObfuscation,             // 20
            tldIsLegit,                 // 21
            domainIsSafe                // 22
        };
    }
    
    /**
     * Get feature names in extraction order (22 features)
     */
    public static List<String> getComprehensiveFeatureNames() {
        return Arrays.asList(
            "URLLength",
            "DomainLength",
            "TLDLength",
            "IsDomainIP",
            "NoOfSubDomain",
            "IsHTTPS",
            "NoOfLettersInURL",
            "NoOfDigitsInURL",
            "NoOfEqualsInURL",
            "NoOfQMarkInURL",
            "NoOfAmpersandInURL",
            "NoOfOtherSpecialCharsInURL",
            "LetterRatioInURL",
            "DigitRatioInURL",
            "SpecialCharRatioInURL",
            "CharContinuationRate",
            "URLCharProb",
            "DomainHasHyphen",
            "URLHasDblSlash",
            "HasObfuscation",
            "TLDIsLegitimate",
            "DomainIsKnownSafe"
        );
    }
    
    /**
     * Get feature count
     */
    public static int getFeatureCount() {
        return 22;
    }
    
    /**
     * Validate extracted features
     */
    public static boolean validateFeatures(float[] features) {
        if (features == null || features.length != 22) {
            return false;
        }
        
        // Check binary features (should be 0.0 or 1.0)
        int[] binaryIndices = {3, 4, 5, 18, 19, 20, 21};  // IsDomainIP, Subdomains, IsHTTPS, etc.
        for (int idx : new int[]{3, 5, 18, 20, 21}) {
            if (features[idx] != 0.0f && features[idx] != 1.0f) {
                return false;
            }
        }
        
        // All features should be non-negative
        for (float feature : features) {
            if (feature < 0) {
                return false;
            }
        }
        
        return true;
    }
    
    // ========== HELPER METHODS ==========
    
    private static String extractDomain(String url) {
        try {
            // Remove protocol
            if (url.contains("://")) {
                url = url.substring(url.indexOf("://") + 3);
            }
            // Remove path
            if (url.contains("/")) {
                url = url.substring(0, url.indexOf("/"));
            }
            // Remove port
            if (url.contains(":")) {
                url = url.substring(0, url.indexOf(":"));
            }
            return url.toLowerCase();
        } catch (Exception e) {
            return url.toLowerCase();
        }
    }
    
    private static boolean isIpAddress(String domain) {
        // IPv4
        if (IPV4_PATTERN.matcher(domain).find()) {
            return true;
        }
        // IPv6
        return domain.contains("::") || IPV6_PATTERN.matcher(domain).find();
    }
    
    private static float countCharType(String str, java.util.function.Predicate<Character> predicate) {
        float count = 0;
        for (char c : str.toCharArray()) {
            if (predicate.test(c)) {
                count++;
            }
        }
        return count;
    }
    
    private static float countOccurrence(String str, char ch) {
        float count = 0;
        for (char c : str.toCharArray()) {
            if (c == ch) {
                count++;
            }
        }
        return count;
    }
    
    private static int countDblSlash(String str) {
        int count = 0;
        for (int i = 0; i < str.length() - 1; i++) {
            if (str.charAt(i) == '/' && str.charAt(i + 1) == '/') {
                count++;
            }
        }
        return count;
    }
    
    private static float countSpecialChars(String str) {
        float count = 0;
        for (char c : str.toCharArray()) {
            if (!Character.isLetterOrDigit(c)) {
                count++;
            }
        }
        return count;
    }
    
    private static float countOtherSpecialChars(String str) {
        float count = 0;
        String excluded = ":/?#@=&-.!~*'()[]";
        for (char c : str.toCharArray()) {
            if (!Character.isLetterOrDigit(c) && excluded.indexOf(c) < 0) {
                count++;
            }
        }
        return count;
    }
    
    private static int getMaxConsecutiveChar(String str) {
        if (str.isEmpty()) return 0;
        int maxCount = 1;
        int currentCount = 1;
        
        for (int i = 1; i < str.length(); i++) {
            if (str.charAt(i) == str.charAt(i - 1)) {
                currentCount++;
                maxCount = Math.max(maxCount, currentCount);
            } else {
                currentCount = 1;
            }
        }
        return maxCount;
    }
    
    private static float calculateEntropy(String str) {
        if (str.isEmpty()) return 0.0f;
        
        // Count character frequencies
        Map<Character, Integer> freq = new HashMap<>();
        for (char c : str.toCharArray()) {
            freq.put(c, freq.getOrDefault(c, 0) + 1);
        }
        
        // Calculate Shannon entropy
        double entropy = 0.0;
        for (int count : freq.values()) {
            double probability = (double) count / str.length();
            if (probability > 0) {
                entropy -= probability * (Math.log(probability) / Math.log(2));
            }
        }
        
        return (float) entropy;
    }
    
    private static boolean detectObfuscation(String url) {
        // Punycode detection
        if (url.toLowerCase().contains("xn--")) {
            return true;
        }
        
        // Percent encoding count
        int percentEncoded = 0;
        for (int i = 0; i < url.length() - 2; i++) {
            if (url.charAt(i) == '%' && 
                Character.isDigit(url.charAt(i + 1)) && 
                Character.isDigit(url.charAt(i + 2))) {
                percentEncoded++;
            }
        }
        return percentEncoded > 3;
    }
    
    private static boolean isKnownSafeDomain(String domain) {
        domain = domain.toLowerCase();
        
        // Exact match
        if (KNOWN_SAFE_DOMAINS.contains(domain)) {
            return true;
        }
        
        // Subdomain match (e.g., mail.google.com → google.com)
        String[] parts = domain.split("\\.");
        if (parts.length > 2) {
            String baseDomain = parts[parts.length - 2] + "." + parts[parts.length - 1];
            return KNOWN_SAFE_DOMAINS.contains(baseDomain);
        }
        
        return false;
    }
}
