"""
Enhanced Feature Extractor for Level-1 with Domain Intelligence
Reduces false positives by incorporating domain legitimacy
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Tuple
from domain_whitelist import (
    is_known_legitimate_domain,
    is_legitimate_tld,
    is_suspicious_tld,
    get_domain_from_url,
    get_tld,
    get_subdomain_count,
    get_domain_length
)


def extract_enhanced_features(url: str) -> Tuple[List[float], Dict]:
    """
    Extract 12 enhanced URL + domain features for Level-1 analysis.
    These features include domain legitimacy checks to reduce false positives.
    
    Features:
    1. url_length - Length of URL
    2. dot_count - Dots in URL
    3. hyphen_count - Hyphens in URL
    4. special_char_count - Special characters (#,$,%,&,etc)
    5. has_https - HTTPS presence (1=yes, 0=no)
    6. has_ip - IP address in URL (1=yes, 0=no)
    7. suspicious_keyword_count - Phishing keywords
    8. is_known_legitimate_domain - Domain in whitelist (1=yes, 0=no)
    9. is_legitimate_tld - Known good TLD (1=yes, 0=no)
    10. is_suspicious_tld - Suspicious TLD (1=yes, 0=no)
    11. subdomain_count - Number of subdomains
    12. query_param_count - Number of query parameters
    
    Returns:
        Tuple of (feature_vector, feature_dict)
    """
    
    url = url.strip()
    
    # Original 7 features
    url_length = float(len(url))
    dot_count = float(url.count('.'))
    hyphen_count = float(url.count('-'))
    
    special_chars = r'[@#$%&*+=?!~^()\[\]{}|\\:;"\'<>]'
    special_char_count = float(len(re.findall(special_chars, url)))
    
    has_https = 1.0 if url.startswith('https://') else 0.0
    has_ip = 1.0 if _contains_ip_address(url) else 0.0
    suspicious_keyword_count = float(_count_suspicious_keywords(url))
    
    # New domain-based features
    is_known_safe = 1.0 if is_known_legitimate_domain(url) else 0.0
    
    tld = get_tld(url)
    is_legit_tld = 1.0 if is_legitimate_tld(tld) else 0.0
    is_suspicious_tld_flag = 1.0 if is_suspicious_tld(tld) else 0.0
    
    subdomain_count = float(get_subdomain_count(url))
    
    # Query parameter count
    query_param_count = float(_count_query_params(url))
    
    features = [
        url_length,
        dot_count,
        hyphen_count,
        special_char_count,
        has_https,
        has_ip,
        suspicious_keyword_count,
        is_known_safe,           # NEW: Domain whitelist
        is_legit_tld,           # NEW: TLD legitimacy
        is_suspicious_tld_flag, # NEW: Suspicious TLD
        subdomain_count,        # NEW: Subdomain count
        query_param_count       # NEW: Query parameters
    ]
    
    feature_dict = {
        'url_length': url_length,
        'dot_count': dot_count,
        'hyphen_count': hyphen_count,
        'special_char_count': special_char_count,
        'has_https': has_https,
        'has_ip': has_ip,
        'suspicious_keyword_count': suspicious_keyword_count,
        'is_known_legitimate_domain': is_known_safe,
        'is_legitimate_tld': is_legit_tld,
        'is_suspicious_tld': is_suspicious_tld_flag,
        'subdomain_count': subdomain_count,
        'query_param_count': query_param_count
    }
    
    return features, feature_dict


def get_enhanced_feature_names() -> List[str]:
    """Get feature names in extraction order"""
    return [
        'url_length',
        'dot_count',
        'hyphen_count',
        'special_char_count',
        'has_https',
        'has_ip',
        'suspicious_keyword_count',
        'is_known_legitimate_domain',
        'is_legitimate_tld',
        'is_suspicious_tld',
        'subdomain_count',
        'query_param_count'
    ]


def _contains_ip_address(url: str) -> bool:
    """Detect if URL contains IPv4 or IPv6 address"""
    ipv4_pattern = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    if re.search(ipv4_pattern, url):
        return True
    if '::' in url or re.search(r'[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}', url):
        return True
    return False


SUSPICIOUS_KEYWORDS = {
    'phish', 'login', 'signin', 'verify', 'update', 'confirm', 'account',
    'secure', 'banking', 'paypal', 'amazon', 'apple', 'microsoft', 'fake',
    'clone', 'bit.ly', 'tinyurl', 'short', 'click', 'urgent', 'alert',
    'suspend', 'activity', 'unusual'
}


def _count_suspicious_keywords(url: str) -> int:
    """Count suspicious keywords in URL"""
    url_lower = url.lower()
    count = 0
    for keyword in SUSPICIOUS_KEYWORDS:
        count += url_lower.count(keyword)
    return count


def _count_query_params(url: str) -> int:
    """Count number of query parameters in URL"""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return 0
        # Count occurrences of & + 1 for base param
        return len(parsed.query.split('&'))
    except:
        return 0


# Test function to show how this fixes false positives
def test_enhanced_features():
    """Test the enhanced extractor on the problematic URLs"""
    
    problematic_urls = [
        'https://chatgpt.com/c/6980f14c-155c-8321-9040-72916653b683',
        'https://discord.com/channels/@me/1471875630390972468',
        'https://www.youtube.com/watch?v=3EI9YAySwHQ&list=PLqM7alHXFySEgUZPe57fURJrIt6rXZisW&index=27',
        'https://google.com',
        'https://github.com/dinesh-naragani/web-integrity-shield'
    ]
    
    print("\n=== Enhanced Feature Extraction Test ===\n")
    for url in problematic_urls:
        features, feature_dict = extract_enhanced_features(url)
        print(f"URL: {url}")
        print(f"  is_known_legitimate_domain: {feature_dict['is_known_legitimate_domain']} (1=recognized safe domain)")
        print(f"  is_legitimate_tld: {feature_dict['is_legitimate_tld']} (1=good TLD)")
        print(f"  suspicious_keyword_count: {feature_dict['suspicious_keyword_count']}")
        print(f"  query_param_count: {feature_dict['query_param_count']}")
        print()


if __name__ == "__main__":
    test_enhanced_features()
