"""
Enhanced Hybrid Phishing Detection
Combines:
1. Domain whitelist (known legitimate sites)
2. Phishing rules (suspicious patterns)
3. ML model (for borderline cases)
"""

import os
import pickle
import json
import re
from urllib.parse import urlparse


# Whitelist of known legitimate domains
KNOWN_LEGITIMATE_DOMAINS = {
    'google.com', 'gmail.com', 'youtube.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'github.com', 'stackoverflow.com', 'reddit.com', 'linkedin.com',
    'amazon.com', 'ebay.com', 'paypal.com', 'microsoft.com', 'apple.com',
    'netflix.com', 'discord.com', 'twitch.tv', 'slack.com', 'dropbox.com',
    'notion.so', 'figma.com', 'adobe.com', 'spotify.com', 'wikipedia.org',
    'chatgpt.com', 'openai.com', 'anthropic.com', 'gemini.google.com', 'claude.ai'
}

# Suspicious TLDs commonly used in phishing
SUSPICIOUS_TLDS = {
    'tk', 'ga', 'ml', 'cf', 'gq',  # Free hosting TLDs
    'top', 'loan', 'download', 'science', 'stream',  # Generic abuse TLDs
    're', 'men', 'works', 'phone', 'webcam'
}

# Known brands to check for typosquatting
BRAND_NAMES = {
    'paypal', 'amazon', 'apple', 'google', 'facebook', 'microsoft', 'netflix',
    'ebay', 'linkedin', 'twitter', 'instagram', 'youtube', 'github'
}

# Suspicious patterns in domain names
SUSPICIOUS_PATTERNS = [
    r'verify|confirm|secure|update|alert|validate|authenticate',
    r'login|signin|account|password|credentials|reset|recovery',
    r'click|urgent|action|required|expired|confirm',
    r'payment|billing|subscription|refund|claim|prize'
]


class HybridPhishingDetector:
    """Enhanced hybrid phishing detector using rules + whitelist + ML"""
    
    def __init__(self, model_path=None, scaler_path=None):
        """Initialize detector with optional ML model and scaler"""
        self.model = None
        self.scaler = None
        self.feature_extractor = None
        
        if model_path and os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
        
        if scaler_path and os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
        
        # Lazy load feature extractor only when needed
        self._feature_extractor = None
    
    @property
    def feature_extractor_module(self):
        """Lazy load feature extractor"""
        if self._feature_extractor is None:
            from comprehensive_feature_extractor import extract_comprehensive_features
            self._feature_extractor = extract_comprehensive_features
        return self._feature_extractor
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain.lower()
        except:
            return ""
    
    def _get_tld(self, domain):
        """Get TLD from domain"""
        try:
            parts = domain.split('.')
            if len(parts) >= 2:
                # Handle special cases like .co.uk
                if len(parts) >= 3 and parts[-2] == 'co':
                    return f"{parts[-2]}.{parts[-1]}"
                return parts[-1]
            return ""
        except:
            return ""
    
    def _is_ip_address(self, host):
        """Check if host is an IP address"""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, host))
    
    def _calculate_typosquatting_score(self, domain, brand_list=BRAND_NAMES):
        """Calculate typosquatting likelihood using Levenshtein distance"""
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # Extract main part of domain (before first dot)
        main_part = domain.split('.')[0].lower()
        
        min_distance = float('inf')
        for brand in brand_list:
            distance = levenshtein_distance(main_part, brand)
            min_distance = min(min_distance, distance)
        
        # If main part is 1-2 chars different from a brand, likely typosquatting
        return min_distance <= 2
    
    def _check_suspicious_patterns(self, url):
        """Check for suspicious patterns in URL"""
        url_lower = url.lower()
        
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    def detect_phishing(self, url):
        """
        Hybrid phishing detection
        Returns: (verdict, confidence, reason)
            verdict: "PHISHING" or "LEGITIMATE"
            confidence: 0.0-1.0
            reason: explanation of decision
        """
        
        domain = self._extract_domain(url)
        tld = self._get_tld(domain)
        host = urlparse(url).netloc
        
        # Rule 1: Check domain whitelist
        if domain in KNOWN_LEGITIMATE_DOMAINS:
            return ("LEGITIMATE", 0.99, "Known legitimate domain")
        
        # Check subdomain whitelist (e.g., mail.google.com -> google.com)
        parts = domain.split('.')
        if len(parts) > 2:
            main_domain = '.'.join(parts[-2:])
            if main_domain in KNOWN_LEGITIMATE_DOMAINS:
                return ("LEGITIMATE", 0.95, "Known legitimate parent domain")
        
        # Rule 2: Check for IP-based URLs (high phishing indicator)
        if self._is_ip_address(host.split(':')[0]):
            return ("PHISHING", 0.95, "IP-based URL (suspicious)")
        
        # Rule 3: Check for suspicious TLDs
        if tld in SUSPICIOUS_TLDS:
            return ("PHISHING", 0.90, f"Suspicious TLD: .{tld}")
        
        # Rule 4: Check for typosquatting
        if self._calculate_typosquatting_score(domain):
            return ("PHISHING", 0.85, "Possible typosquatting (similar to known brand)")
        
        # Rule 5: Check for suspicious patterns
        if self._check_suspicious_patterns(url):
            return ("PHISHING", 0.75, "Suspicious URL pattern")
        
        # Rule 6: Use ML model if available
        if self.model and self.scaler:
            try:
                features, _ = self.feature_extractor_module(url)
                features_scaled = self.scaler.transform([features])
                pred_proba = self.model.predict_proba(features_scaled)[0]
                model_risk = pred_proba[1]
                
                # If model confidence is high, use it
                if model_risk > 0.9 or model_risk < 0.1:
                    verdict = "PHISHING" if model_risk > 0.5 else "LEGITIMATE"
                    return (verdict, model_risk, f"ML model prediction (confidence: {model_risk:.2f})")
            except:
                pass
        
        # Default: if no rules triggered, consider legitimate
        return ("LEGITIMATE", 0.5, "No suspicious patterns detected")


def test_detector():
    """Test the hybrid detector"""
    
    print("\n" + "=" * 80)
    print("HYBRID PHISHING DETECTOR - TEST SUITE")
    print("=" * 80 + "\n")
    
    # Try to load models
    detector = HybridPhishingDetector(
        'models/level1_xgboost_22features.pkl',
        'models/level1_scaler_22features.pkl'
    )
    
    test_cases = [
        # Legitimate - known domains
        ("https://www.chatgpt.com", "LEGITIMATE"),
        ("https://discord.com", "LEGITIMATE"),
        ("https://www.youtube.com", "LEGITIMATE"),
        ("https://github.com", "LEGITIMATE"),
        ("https://www.google.com", "LEGITIMATE"),
        ("https://mail.google.com/mail", "LEGITIMATE"),
        ("https://accounts.google.com/signin", "LEGITIMATE"),
        ("https://example-startup.com", "LEGITIMATE"),
        
        # Phishing - various patterns
        ("http://paypa1.com/verify-account", "PHISHING"),
        ("http://45.77.12.99/login?session=abc", "PHISHING"),
        ("http://secure-login-paypal-verify.tk/account", "PHISHING"),
        ("http://apple-id-security-update.ga/login", "PHISHING"),
        ("https://secure-amazon-login-verify.ml/account", "PHISHING"),
        ("http://192.168.1.1/admin", "PHISHING"),
        ("http://gogle.com/verify", "PHISHING"),
        ("https://paypa1.com/confirm-payment", "PHISHING"),
    ]
    
    correct = 0
    
    for url, expected in test_cases:
        verdict, confidence, reason = detector.detect_phishing(url)
        is_correct = (verdict == expected)
        status = "✓" if is_correct else "✗"
        
        if is_correct:
            correct += 1
        
        print(f"{status} {url:60s}")
        print(f"   Expected: {expected:12s} | Got: {verdict:12s} | Confidence: {confidence:.2f}")
        print(f"   Reason: {reason}\n")
    
    print("=" * 80)
    print(f"Accuracy: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.1f}%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_detector()
