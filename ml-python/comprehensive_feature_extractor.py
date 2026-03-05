"""
Comprehensive URL Feature Extractor for Level-1 Analysis
Extracts 22 features from URLs to build robust phishing detection models.
Features are designed to NOT overfit - they're statistically independent and meaningful.

Features extracted (in order):
1.  URLLength - Total length of the URL
2.  DomainLength - Length of domain name (without TLD)
3.  TLDLength - Length of top-level domain
4.  IsDomainIP - Binary: is domain an IP address? (1=yes, 0=no)
5.  NoOfSubDomain - Count of subdomains (e.g., api.v2.example.com = 2 subdomains)
6.  IsHTTPS - Binary: uses HTTPS? (1=yes, 0=no)
7.  NoOfLettersInURL - Count of alphabetic characters
8.  NoOfDigitsInURL - Count of numeric characters
9.  NoOfEqualsInURL - Count of '=' characters
10. NoOfQMarkInURL - Count of '?' characters
11. NoOfAmpersandInURL - Count of '&' characters
12. NoOfOtherSpecialCharsInURL - Count of other special chars
13. LetterRatioInURL - Ratio of letters to total URL length
14. DigitRatioInURL - Ratio of digits to total URL length
15. SpecialCharRatioInURL - Ratio of special chars to total URL length
16. CharContinuationRate - Longest consecutive identical character
17. URLCharProb - Shannon entropy of character distribution
18. DomainHasHyphen - Binary: domain contains hyphen? (1=yes, 0=no)
19. URLHasDblSlash - Count of '//' occurrences (should be 1 for normal URLs)
20. HasObfuscation - Binary: obfuscated characters detected? (1=yes, 0=no)
21. TLDIsLegitimate - Binary: TLD is known legitimate? (1=yes, 0=no)
22. DomainIsKnownSafe - Binary: domain in whitelist? (1=yes, 0=no)
"""

import re
import math
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Tuple
from collections import Counter


# Legitimate TLDs
LEGITIMATE_TLDS = {
    'com', 'org', 'net', 'edu', 'gov', 'co.uk', 'co.jp', 'de', 'fr',
    'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi',
    'io', 'ai', 'dev', 'app', 'tech', 'cloud', 'digital'
}

# Top legitimate domains whitelist
KNOWN_SAFE_DOMAINS = {
    'google.com', 'facebook.com', 'microsoft.com', 'apple.com', 'amazon.com',
    'youtube.com', 'gmail.com', 'github.com', 'stackoverflow.com', 'wikipedia.org',
    'discord.com', 'slack.com', 'telegram.org', 'twitter.com', 'reddit.com',
    'chatgpt.com', 'openai.com', 'claude.ai', 'netflix.com', 'linkedin.com',
    'instagram.com', 'twitch.tv', 'paypal.com', 'stripe.com', 'heroku.com',
    'aws.amazon.com', 'cloud.google.com', 'azure.microsoft.com'
}


def extract_comprehensive_features(url: str) -> Tuple[List[float], Dict]:
    """
    Extract 22 comprehensive features from URL for robust Level-1 detection.
    
    These features are:
    - Statistically independent (minimal correlation)
    - Meaningful for phishing detection (not arbitrary)
    - Resistant to overfitting (avoid highly correlated features)
    - Calculated from URL structure only (no network requests)
    
    Args:
        url: The URL string to analyze
        
    Returns:
        Tuple of (feature_vector, feature_dict)
    """
    
    url = url.strip()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove www prefix for analysis
    if domain.startswith('www.'):
        domain_clean = domain[4:]
    else:
        domain_clean = domain
    
    # Extract TLD
    domain_parts = domain_clean.split('.')
    tld = domain_parts[-1] if len(domain_parts) > 0 else ""
    
    # Feature 1: URL Length
    url_length = float(len(url))
    
    # Feature 2: Domain Length (without TLD)
    if len(domain_parts) >= 2:
        domain_name = '.'.join(domain_parts[:-1])
        domain_length = float(len(domain_name))
    else:
        domain_length = float(len(domain_clean))
    
    # Feature 3: TLD Length
    tld_length = float(len(tld))
    
    # Feature 4: Is Domain IP? (1=yes, 0=no)
    is_domain_ip = 1.0 if _is_ip_address(domain) else 0.0
    
    # Feature 5: Number of Subdomains
    # Count dots in domain minus the main domain
    num_subdomains = float(domain.count('.') - 1) if '.' in domain else 0.0
    
    # Feature 6: Is HTTPS? (1=yes, 0=no)
    is_https = 1.0 if url.startswith('https://') else 0.0
    
    # Feature 7: Number of Letters
    num_letters = float(sum(1 for c in url if c.isalpha()))
    
    # Feature 8: Number of Digits
    num_digits = float(sum(1 for c in url if c.isdigit()))
    
    # Feature 9: Number of '='
    num_equals = float(url.count('='))
    
    # Feature 10: Number of '?'
    num_qmark = float(url.count('?'))
    
    # Feature 11: Number of '&'
    num_ampersand = float(url.count('&'))
    
    # Feature 12: Number of Other Special Chars
    # Count all special chars except: :, /, ?, #, @, =, &, -, ., !, ~, *, ', (, )
    other_special_pattern = r'[^a-zA-Z0-9:/?#@=&\-\.!\~\*\'()\[\]]'
    num_other_special = float(len(re.findall(other_special_pattern, url)))
    
    # Feature 13: Letter Ratio
    letter_ratio = num_letters / url_length if url_length > 0 else 0.0
    
    # Feature 14: Digit Ratio
    digit_ratio = num_digits / url_length if url_length > 0 else 0.0
    
    # Feature 15: Special Character Ratio
    special_pattern = r'[^a-zA-Z0-9]'
    num_special = float(len(re.findall(special_pattern, url)))
    special_ratio = num_special / url_length if url_length > 0 else 0.0
    
    # Feature 16: Character Continuation Rate (longest consecutive identical char)
    char_continuation = float(_get_max_consecutive_char(url))
    
    # Feature 17: URL Character Probability (Shannon Entropy)
    char_entropy = _calculate_entropy(url)
    
    # Feature 18: Domain Has Hyphen? (1=yes, 0=no)
    domain_has_hyphen = 1.0 if '-' in domain_clean else 0.0
    
    # Feature 19: URL Has Double Slash (// count)
    # Normal URLs have 1 (//) but phishing might have more
    double_slash_count = float(url.count('//'))
    
    # Feature 20: Has Obfuscation? (unusual UTF-8, punycode, etc.)
    has_obfuscation = 1.0 if _has_obfuscation(url) else 0.0
    
    # Feature 21: TLD Is Legitimate? (1=yes, 0=no)
    tld_is_legitimate = 1.0 if tld.lower() in LEGITIMATE_TLDS else 0.0
    
    # Feature 22: Domain Is Known Safe? (1=yes, 0=no)
    domain_is_safe = 1.0 if domain_clean in KNOWN_SAFE_DOMAINS else 0.0
    
    # Build feature vector in fixed order
    features = [
        url_length,
        domain_length,
        tld_length,
        is_domain_ip,
        num_subdomains,
        is_https,
        num_letters,
        num_digits,
        num_equals,
        num_qmark,
        num_ampersand,
        num_other_special,
        letter_ratio,
        digit_ratio,
        special_ratio,
        char_continuation,
        char_entropy,
        domain_has_hyphen,
        double_slash_count,
        has_obfuscation,
        tld_is_legitimate,
        domain_is_safe
    ]
    
    feature_dict = {
        'URLLength': url_length,
        'DomainLength': domain_length,
        'TLDLength': tld_length,
        'IsDomainIP': is_domain_ip,
        'NoOfSubDomain': num_subdomains,
        'IsHTTPS': is_https,
        'NoOfLettersInURL': num_letters,
        'NoOfDigitsInURL': num_digits,
        'NoOfEqualsInURL': num_equals,
        'NoOfQMarkInURL': num_qmark,
        'NoOfAmpersandInURL': num_ampersand,
        'NoOfOtherSpecialCharsInURL': num_other_special,
        'LetterRatioInURL': letter_ratio,
        'DigitRatioInURL': digit_ratio,
        'SpecialCharRatioInURL': special_ratio,
        'CharContinuationRate': char_continuation,
        'URLCharProb': char_entropy,
        'DomainHasHyphen': domain_has_hyphen,
        'URLHasDblSlash': double_slash_count,
        'HasObfuscation': has_obfuscation,
        'TLDIsLegitimate': tld_is_legitimate,
        'DomainIsKnownSafe': domain_is_safe
    }
    
    return features, feature_dict


def get_feature_names() -> List[str]:
    """Get feature names in extraction order"""
    return [
        'URLLength',
        'DomainLength',
        'TLDLength',
        'IsDomainIP',
        'NoOfSubDomain',
        'IsHTTPS',
        'NoOfLettersInURL',
        'NoOfDigitsInURL',
        'NoOfEqualsInURL',
        'NoOfQMarkInURL',
        'NoOfAmpersandInURL',
        'NoOfOtherSpecialCharsInURL',
        'LetterRatioInURL',
        'DigitRatioInURL',
        'SpecialCharRatioInURL',
        'CharContinuationRate',
        'URLCharProb',
        'DomainHasHyphen',
        'URLHasDblSlash',
        'HasObfuscation',
        'TLDIsLegitimate',
        'DomainIsKnownSafe'
    ]


def _is_ip_address(domain: str) -> bool:
    """Check if domain is an IP address (IPv4 or IPv6)"""
    # IPv4
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ipv4_pattern, domain):
        return True
    
    # IPv6
    if '::' in domain or re.match(r'^[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}', domain):
        return True
    
    return False


def _get_max_consecutive_char(s: str) -> int:
    """Get the longest sequence of consecutive identical characters"""
    if not s:
        return 0
    
    max_count = 1
    current_count = 1
    
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 1
    
    return max_count


def _calculate_entropy(s: str) -> float:
    """
    Calculate Shannon entropy of character distribution.
    Higher entropy = more diverse character distribution
    Lower entropy = repeated characters (phishing indicator)
    
    Range: 0 to ~5.5 for ASCII
    """
    if not s:
        return 0.0
    
    # Count character frequencies
    char_counts = Counter(s)
    
    # Calculate entropy
    entropy = 0.0
    for count in char_counts.values():
        probability = count / len(s)
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def _has_obfuscation(url: str) -> bool:
    """
    Detect obfuscation attempts:
    - Punycode encoded domains (xn--)
    - High number of encoded characters (%xx)
    - Mixed scripts (unusual Unicode)
    """
    
    # Punycode detection
    if 'xn--' in url.lower():
        return True
    
    # Percent encoding count
    percent_encoded = len(re.findall(r'%[0-9A-Fa-f]{2}', url))
    if percent_encoded > 3:  # More than 3 encoded chars is suspicious
        return True
    
    # Try to detect non-ASCII characters
    try:
        url.encode('ascii')
    except UnicodeEncodeError:
        # Contains non-ASCII characters
        return True
    
    return False


# Test and demonstration
def demo_feature_extraction():
    """Demonstrate feature extraction on example URLs"""
    
    test_urls = [
        'https://chatgpt.com/c/6980f14c-155c-8321-9040-72916653b683',
        'https://discord.com/channels/@me/1471875630390972468',
        'https://www.youtube.com/watch?v=3EI9YAySwHQ&list=PLqM7alHXFySEgUZPe57fURJrIt6rXZisW&index=27',
        'https://google.com',
        'https://github.com/dinesh-naragani/web-integrity-shield',
        'http://phishing-site-12345.tk/login.php?id=abc123&token=xyz789',
        'http://192.168.1.1/admin/login',
    ]
    
    print("\n" + "="*80)
    print("COMPREHENSIVE URL FEATURE EXTRACTION DEMO")
    print("="*80 + "\n")
    
    for url in test_urls:
        features, feature_dict = extract_comprehensive_features(url)
        print(f"URL: {url}")
        print(f"  URLLength: {feature_dict['URLLength']}")
        print(f"  DomainIsKnownSafe: {feature_dict['DomainIsKnownSafe']} (1=recognized safe)")
        print(f"  TLDIsLegitimate: {feature_dict['TLDIsLegitimate']} (1=good TLD)")
        print(f"  IsDomainIP: {feature_dict['IsDomainIP']}")
        print(f"  CharContinuationRate: {feature_dict['CharContinuationRate']}")
        print(f"  URLCharProb (entropy): {feature_dict['URLCharProb']:.3f}")
        print(f"  SpecialCharRatioInURL: {feature_dict['SpecialCharRatioInURL']:.3f}")
        print()


if __name__ == "__main__":
    demo_feature_extraction()
