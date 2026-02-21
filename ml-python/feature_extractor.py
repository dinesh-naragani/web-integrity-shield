"""
Feature Extractor for Phishing URLs
Deterministic extraction of URL features for Level-1 ML model.

Features (in fixed order):
1. url_length - Length of the URL
2. dot_count - Number of dots in URL
3. hyphen_count - Number of hyphens in URL
4. special_char_count - Number of special characters
5. has_https - Binary: 1 if HTTPS, 0 otherwise
6. has_ip - Binary: 1 if IP address detected, 0 otherwise
7. suspicious_keyword_count - Count of suspicious keywords

This feature order must match between training (Python) and inference (Java).
All features are normalized/extracted deterministically.
"""

import re
import urllib.parse
from typing import List, Dict, Tuple


# Suspicious keywords commonly found in phishing URLs
SUSPICIOUS_KEYWORDS = {
    'phish',
    'login',
    'signin',
    'verify',
    'update',
    'confirm',
    'account',
    'secure',
    'banking',
    'paypal',
    'amazon',
    'apple',
    'microsoft',
    'fake',
    'clone',
    'bit.ly',
    'tinyurl',
    'short',
    'click',
    'urgent',
    'alert',
    'suspend',
    'activity',
    'unusual'
}


def extract_features(url: str) -> Tuple[List[float], Dict]:
    """
    Extract features from a URL in deterministic order.
    
    Args:
        url: The URL string to analyze
        
    Returns:
        Tuple of (feature_vector, feature_dict)
        - feature_vector: List of 7 float values in fixed order
        - feature_dict: Dictionary with feature names for debugging
    """
    
    # Normalize URL: strip whitespace
    url = url.strip()
    
    # Feature 1: URL Length
    url_length = len(url)
    
    # Feature 2: Dot Count (excluding domain dots)
    dot_count = url.count('.')
    
    # Feature 3: Hyphen Count
    hyphen_count = url.count('-')
    
    # Feature 4: Special Character Count
    # Count: @, #, $, %, &, *, +, =, ?, !, ~, ^, (, ), [, ], {, }, |, \, :, ;, '"', <, >
    special_chars = r'[@#$%&*+=?!~^()\[\]{}|\\:;"\'<>]'
    special_char_count = len(re.findall(special_chars, url))
    
    # Feature 5: HTTPS Presence (0 or 1)
    has_https = 1.0 if url.startswith('https://') else 0.0
    
    # Feature 6: IP Address Presence (0 or 1)
    has_ip = 1.0 if _contains_ip_address(url) else 0.0
    
    # Feature 7: Suspicious Keyword Count
    suspicious_keyword_count = _count_suspicious_keywords(url)
    
    # Fixed order vector: MUST match Java extraction
    features = [
        float(url_length),
        float(dot_count),
        float(hyphen_count),
        float(special_char_count),
        has_https,
        has_ip,
        float(suspicious_keyword_count)
    ]
    
    # Debug dictionary
    feature_dict = {
        'url_length': url_length,
        'dot_count': dot_count,
        'hyphen_count': hyphen_count,
        'special_char_count': special_char_count,
        'has_https': has_https,
        'has_ip': has_ip,
        'suspicious_keyword_count': suspicious_keyword_count
    }
    
    return features, feature_dict


def _contains_ip_address(url: str) -> bool:
    """
    Detect if URL contains an IP address (IPv4 or IPv6).
    
    IPv4 pattern: 0-255.0-255.0-255.0-255
    IPv6 pattern: Simplified detection for colons (::)
    """
    
    # IPv4 pattern: 0-255.0-255.0-255.0-255
    ipv4_pattern = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    
    if re.search(ipv4_pattern, url):
        return True
    
    # IPv6 check: simple heuristic for "::" pattern
    if '::' in url or re.search(r'[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}', url):
        return True
    
    return False


def _count_suspicious_keywords(url: str) -> int:
    """
    Count occurrences of suspicious keywords in the URL.
    Case-insensitive.
    """
    url_lower = url.lower()
    count = 0
    
    for keyword in SUSPICIOUS_KEYWORDS:
        count += url_lower.count(keyword)
    
    return count


def get_feature_names() -> List[str]:
    """
    Return list of feature names in the exact order used by extract_features().
    
    This is critical for model training and inference consistency.
    Must match Java implementation.
    """
    return [
        'url_length',
        'dot_count',
        'hyphen_count',
        'special_char_count',
        'has_https',
        'has_ip',
        'suspicious_keyword_count'
    ]


def validate_features(features: List[float]) -> bool:
    """
    Validate that extracted features are in expected ranges.
    
    Returns:
        True if valid, False otherwise
    """
    if len(features) != 7:
        return False
    
    # Binary features (indices 4, 5) should be 0 or 1
    if features[4] not in [0.0, 1.0]:
        return False
    if features[5] not in [0.0, 1.0]:
        return False
    
    # All features should be non-negative
    for feature in features:
        if feature < 0:
            return False
    
    return True


# Example usage
if __name__ == '__main__':
    test_urls = [
        'https://www.google.com',
        'http://192.168.1.1/admin',
        'https://paypal-login-verify.com',
        'http://bit.ly/phishing-click'
    ]
    
    for url in test_urls:
        features, feature_dict = extract_features(url)
        print(f"\nURL: {url}")
        print(f"Features: {features}")
        print(f"Valid: {validate_features(features)}")
        print(f"Details: {feature_dict}")
