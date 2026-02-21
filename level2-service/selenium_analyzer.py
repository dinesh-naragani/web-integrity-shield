"""
Selenium Page Analyzer for Level-2 Deep Analysis

Analyzes URL content using headless Chrome to detect:
1. Login/password forms
2. Hidden input fields
3. External script domains
4. Number of redirects
5. Page title keywords
6. Suspicious iframe usage
7. SSL certificate warnings
"""

import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException
)

logger = logging.getLogger(__name__)


class SeleniumPageAnalyzer:
    """Analyzes web pages using Selenium headless Chrome"""
    
    # Suspicious keywords in page title
    SUSPICIOUS_TITLE_KEYWORDS = {
        'login', 'signin', 'sign in', 'verify', 'confirm', 'verify identity',
        'update', 'urgent', 'action required', 'suspended', 'alert',
        'billing', 'payment', 'credit card', 'social security'
    }
    
    # Known suspicious domains for externally loaded scripts
    SUSPICIOUS_SCRIPT_DOMAINS = {
        'analytics-tracker.', 'ad-network.', 'click-track.', 'redirect-service.',
        'short-url-', 'bitly', 'tinyurl', 'shortened-link'
    }
    
    # Common phishing keywords in form labels
    PHISHING_FORM_KEYWORDS = {
        'password', 'credit card', 'cvv', 'social security', 'verify identity',
        'confirm identity', 'authenticate', 'validate', 'security code'
    }
    
    def __init__(self, headless: bool = True, page_load_timeout: int = 6, script_timeout: int = 6):
        """
        Initialize Selenium Chrome driver
        
        Args:
            headless: Run in headless mode (no UI)
            page_load_timeout: Page load timeout in seconds
            script_timeout: Script execution timeout in seconds
        """
        try:
            self.driver = self._create_driver(headless)
            self.driver.set_page_load_timeout(page_load_timeout)
            self.driver.set_script_timeout(script_timeout)
            self.page_load_timeout = page_load_timeout
            logger.info(f"✓ Chrome driver initialized (headless={headless})")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise
    
    def _create_driver(self, headless: bool) -> webdriver.Chrome:
        """Create Chrome WebDriver with security options"""
        chrome_options = ChromeOptions()
        
        # Headless mode
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Security and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Performance optimizations (but keep JS enabled for form detection)
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-css")
        
        # Disable chrome logging
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-default-apps")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            logger.error(f"Chrome driver creation failed: {str(e)}")
            raise
    
    def analyze_page(self, url: str, level1_score: float) -> Dict:
        """
        Perform deep analysis on URL page content
        
        Args:
            url: URL to analyze
            level1_score: Level-1 ONNX model risk score
        
        Returns:
            Dict with keys: score, verdict, reasons
        """
        reasons = []
        factor_scores = {}
        
        try:
            # Attempt page load with timeout
            logger.debug(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for page to settle
            time.sleep(1)
            
            # Factor 1: Check for login forms
            factor_scores['login_form'] = self._check_login_forms(reasons)
            
            # Factor 2: Check for hidden inputs (suspicious for data theft)
            factor_scores['hidden_inputs'] = self._check_hidden_inputs(reasons)
            
            # Factor 3: Check external script domains
            factor_scores['external_scripts'] = self._check_external_scripts(reasons)
            
            # Factor 4: Check for suspicious redirect patterns (via URL changes)
            factor_scores['url_changes'] = self._check_url_changes(url, reasons)
            
            # Factor 5: Check page title keywords
            factor_scores['title_keywords'] = self._check_title_keywords(reasons)
            
            # Factor 6: Check suspicious iframe usage
            factor_scores['suspicious_iframes'] = self._check_iframes(reasons)
            
            # Factor 7: Check SSL/security indicators (via page analysis)
            factor_scores['security_issues'] = self._check_security_indicators(reasons)
            
            # Factor 8: Check form submission behavior
            factor_scores['form_behavior'] = self._check_form_behavior(reasons)
            
        except TimeoutException:
            logger.warning(f"Page load timeout for: {url}")
            reasons.append("Page load timeout (slow/unresponsive)")
            factor_scores['timeout'] = 0.5
        except Exception as e:
            logger.warning(f"Error analyzing page {url}: {str(e)}")
            reasons.append(f"Analysis error: {str(e)}")
            factor_scores['error'] = 0.3
        
        # Calculate weighted Level-2 score
        level2_score = self._calculate_weighted_score(factor_scores, level1_score)
        
        # Determine final verdict
        verdict = "PHISHING" if level2_score >= 0.75 else "SUSPICIOUS"
        
        return {
            'score': level2_score,
            'verdict': verdict,
            'reasons': reasons,
            'factors': factor_scores
        }
    
    def _check_login_forms(self, reasons: List[str]) -> float:
        """Check for login/password form presence (Higher = more suspicious)"""
        score = 0.0
        try:
            # Check for password inputs
            password_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            if password_inputs:
                reasons.append(f"Password form detected ({len(password_inputs)} field{'s' if len(password_inputs) > 1 else ''})")
                score += 0.3  # Password input present
            
            # Check for login-related labels/text
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                reasons.append(f"Form elements detected ({len(forms)} form{'s' if len(forms) > 1 else ''})")
                score += 0.1
            
            # Check for login link/button
            login_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'login') or contains(text(), 'sign in')]")
            if login_buttons:
                reasons.append("Login prompt/button detected")
                score += 0.1
        
        except Exception as e:
            logger.debug(f"Error checking login forms: {str(e)}")
        
        return min(score, 1.0)
    
    def _check_hidden_inputs(self, reasons: List[str]) -> float:
        """Check for hidden input fields (suspicious for data collection)"""
        score = 0.0
        try:
            hidden_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']")
            if hidden_inputs:
                suspicious_hidden = 0
                for inp in hidden_inputs:
                    try:
                        name = inp.get_attribute('name') or 'unknown'
                        value = inp.get_attribute('value') or ''
                        if any(keyword in name.lower() for keyword in ['token', 'csrf', 'nonce', 'tracking']):
                            suspicious_hidden += 1
                    except StaleElementReferenceException:
                        continue
                
                if suspicious_hidden > 0:
                    reasons.append(f"Suspicious hidden inputs detected ({suspicious_hidden})")
                    score = 0.15
        
        except Exception as e:
            logger.debug(f"Error checking hidden inputs: {str(e)}")
        
        return score
    
    def _check_external_scripts(self, reasons: List[str]) -> float:
        """Check for external script injection"""
        score = 0.0
        try:
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            external_scripts = []
            
            for script in scripts:
                try:
                    src = script.get_attribute('src')
                    if src:
                        parsed = urlparse(src)
                        # Check for suspicious script domains
                        domain = parsed.netloc.lower()
                        if any(suspicious in domain for suspicious in self.SUSPICIOUS_SCRIPT_DOMAINS):
                            external_scripts.append(domain)
                            score += 0.1
                except (StaleElementReferenceException, AttributeError):
                    continue
            
            if external_scripts:
                reasons.append(f"Suspicious external scripts: {', '.join(set(external_scripts))}")
                score = min(score, 0.3)
        
        except Exception as e:
            logger.debug(f"Error checking external scripts: {str(e)}")
        
        return score
    
    def _check_url_changes(self, original_url: str, reasons: List[str]) -> float:
        """Check for URL redirects/changes"""
        score = 0.0
        try:
            current_url = self.driver.current_url
            if current_url != original_url:
                reasons.append(f"URL redirect detected: {original_url} → {current_url}")
                score = 0.2
        except Exception as e:
            logger.debug(f"Error checking URL changes: {str(e)}")
        
        return score
    
    def _check_title_keywords(self, reasons: List[str]) -> float:
        """Check page title for suspicious keywords"""
        score = 0.0
        try:
            title = self.driver.title.lower()
            suspicious_keywords = [kw for kw in self.SUSPICIOUS_TITLE_KEYWORDS if kw in title]
            if suspicious_keywords:
                reasons.append(f"Suspicious keywords in page title: {', '.join(suspicious_keywords)}")
                score = 0.2
        except Exception as e:
            logger.debug(f"Error checking title: {str(e)}")
        
        return score
    
    def _check_iframes(self, reasons: List[str]) -> float:
        """Check for suspicious iframe usage"""
        score = 0.0
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                suspicious_iframes = 0
                for iframe in iframes:
                    try:
                        src = iframe.get_attribute('src') or ''
                        # Check for hidden iframes
                        style = iframe.get_attribute('style') or ''
                        if 'display:none' in style.replace(' ', '') or 'visibility:hidden' in style.replace(' ', ''):
                            suspicious_iframes += 1
                    except StaleElementReferenceException:
                        continue
                
                if len(iframes) > 0:
                    reasons.append(f"Iframes detected ({len(iframes)}, {suspicious_iframes} hidden)")
                    score = 0.1 + (0.15 if suspicious_iframes > 0 else 0)
        
        except Exception as e:
            logger.debug(f"Error checking iframes: {str(e)}")
        
        return score
    
    def _check_security_indicators(self, reasons: List[str]) -> float:
        """Check for security indicators"""
        score = 0.0
        try:
            current_url = self.driver.current_url
            # Check for HTTPS
            if not current_url.startswith('https://'):
                reasons.append("No HTTPS encryption detected")
                score = 0.25
        except Exception as e:
            logger.debug(f"Error checking security: {str(e)}")
        
        return score
    
    def _check_form_behavior(self, reasons: List[str]) -> float:
        """Check form submission behavior"""
        score = 0.0
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                try:
                    action = form.get_attribute('action') or ''
                    method = form.get_attribute('method') or 'GET'
                    # Check if form submission might send data to external site
                    if action and not action.startswith('http'):
                        score += 0.05
                except StaleElementReferenceException:
                    continue
        except Exception as e:
            logger.debug(f"Error checking form behavior: {str(e)}")
        
        return min(score, 0.2)
    
    def _calculate_weighted_score(self, factor_scores: Dict[str, float], level1_score: float) -> float:
        """
        Calculate weighted Level-2 score based on factors.
        
        Normalized weights (total = 1.0):
        - Level-1 carryover: 0.35 (carries forward ONNX decision)
        - Login forms: 0.15
        - External scripts: 0.10
        - Hidden inputs: 0.10
        - Title keywords: 0.08
        - URL redirects: 0.07
        - Iframes: 0.05
        - Security indicators: 0.05
        - Form behavior: 0.05
        - Timeout/Error: 0.00 (already penalized in analysis)
        """
        if not factor_scores:
            return min(level1_score, 1.0)  # Fallback to Level-1 if no factors detected
        
        # Normalized weights (total = 1.0)
        weights = {
            'login_form': 0.15,
            'external_scripts': 0.10,
            'hidden_inputs': 0.10,
            'title_keywords': 0.08,
            'url_changes': 0.07,
            'suspicious_iframes': 0.05,
            'security_issues': 0.05,
            'form_behavior': 0.05,
            'timeout': 0.00,  # Don't double-penalize
            'error': 0.00     # Don't double-penalize
        }
        
        # Calculate factor portion (65% of total)
        factor_score = 0.0
        for factor, weight in weights.items():
            if factor in factor_scores:
                factor_score += factor_scores[factor] * weight
        
        # Combine: 35% Level-1 + 65% factors
        total_score = (level1_score * 0.35) + (factor_score * 0.65)
        
        return min(total_score, 1.0)
    
    def close(self):
        """Close Chrome driver and clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Chrome driver closed")
        except Exception as e:
            logger.error(f"Error closing Chrome driver: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure driver is closed"""
        self.close()
