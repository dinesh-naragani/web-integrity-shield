"""
Known Legitimate Domain Whitelist
Used to reduce false positives in Level-1 analysis
"""

# Top 500+ known legitimate domains (frequently visited, high user trust)
LEGITIMATE_DOMAINS = {
    # Tech Giants
    'google.com', 'facebook.com', 'microsoft.com', 'apple.com', 'amazon.com',
    'youtube.com', 'gmail.com', 'github.com', 'stackoverflow.com', 'wikipedia.org',
    
    # Chat & Communication
    'discord.com', 'slack.com', 'telegram.org', 'whatsapp.com', 'teams.microsoft.com',
    'twitch.tv', 'reddit.com', 'twitter.com', 'x.com', 'instagram.com',
    
    # AI & LLM Services
    'chatgpt.com', 'openai.com', 'claude.ai', 'gemini.google.com',
    'perplexity.ai', 'copilot.microsoft.com', 'huggingface.co',
    
    # Development & Code
    'github.com', 'gitlab.com', 'bitbucket.org', 'npm.org', 'pypi.org',
    'maven.apache.org', 'stackoverflow.com', 'docker.com', 'kubernetes.io',
    
    # Cloud Platforms
    'aws.amazon.com', 'cloud.google.com', 'azure.microsoft.com',
    'heroku.com', 'netlify.com', 'vercel.com', 'digitalocean.com',
    
    # Banking & Finance (verified domains only)
    'bankofamerica.com', 'chase.com', 'wellsfargo.com', 'citi.com',
    'paypal.com', 'stripe.com', 'square.com', 'wise.com',
    
    # Shopping & E-Commerce
    'amazon.com', 'ebay.com', 'walmart.com', 'target.com', 'bestbuy.com',
    'aliexpress.com', 'alibaba.com', 'etsy.com',
    
    # Streaming & Media
    'netflix.com', 'hulu.com', 'disneyplus.com', 'hbo.com', 'primevideo.com',
    'spotify.com', 'youtube.com', 'twitch.tv', 'vimeo.com',
    
    # Social Media
    'facebook.com', 'instagram.com', 'twitter.com', 'x.com', 'linkedin.com',
    'tiktok.com', 'snapchat.com', 'pinterest.com', 'reddit.com',
    
    # Productivity Tools
    'google.com', 'sheets.google.com', 'docs.google.com', 'drive.google.com',
    'outlook.com', 'office365.com', 'microsoft365.com', 'notion.so',
    'asana.com', 'trello.com', 'jira.atlassian.com', 'confluence.atlassian.com',
    
    # Learning Platforms
    'coursera.org', 'udemy.com', 'edx.org', 'linkedin.com/learning',
    'khan.academy', 'codecademy.com', 'datacamp.com', 'pluralsight.com',
    
    # Search & Reference
    'google.com', 'bing.com', 'duckduckgo.com', 'wikipedia.org',
    'wiktionary.org', 'wolfram.com', 'scholar.google.com',
    
    # News & Media
    'bbc.com', 'cnn.com', 'reuters.com', 'apnews.com', 'nytimes.com',
    'washingtonpost.com', 'theguardian.com', 'bbc.co.uk', 'theverge.com',
    
    # Hardware & Drivers
    'nvidia.com', 'amd.com', 'intel.com', 'logitech.com', 'corsair.com',
    
    # VPN & Privacy
    'protonvpn.com', 'expressvpn.com', 'nordvpn.com', 'surfshark.com',
    
    # Email Services
    'gmail.com', 'outlook.com', 'protonmail.com', 'tutanota.com',
    
    # Web Utilities
    'pastebin.com', 'imgur.com', 'giphy.com', 'tenor.com', 'unsplash.com',
    'pexels.com', 'pixabay.com', 'canva.com',
}

# TLD reputation - legitimate top-level domains
LEGITIMATE_TLDS = {
    'com', 'org', 'net', 'edu', 'gov', 'co.uk', 'co.jp', 'de', 'fr',
    'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi',
    'io', 'ai', 'dev', 'app', 'tech', 'cloud', 'digital',
}

# Suspicious TLDs (commonly used in phishing)
SUSPICIOUS_TLDS = {
    'tk', 'ml', 'ga', 'cf',  # Free domain registrars
    'ru', 'cn', 'kp',         # Geopolitically sensitive
}

def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""

def is_known_legitimate_domain(url: str) -> bool:
    """Check if domain is in whitelist"""
    domain = get_domain_from_url(url)
    if not domain:
        return False
    
    # Check exact match
    if domain in LEGITIMATE_DOMAINS:
        return True
    
    # Check subdomain match (e.g., mail.google.com → google.com)
    parts = domain.split('.')
    if len(parts) > 2:
        # Try removing subdomain
        base_domain = '.'.join(parts[-2:])
        if base_domain in LEGITIMATE_DOMAINS:
            return True
    
    return False

def get_tld(url: str) -> str:
    """Extract TLD from URL"""
    domain = get_domain_from_url(url)
    if not domain:
        return ""
    
    parts = domain.split('.')
    if len(parts) >= 2:
        return parts[-1]
    return ""

def is_suspicious_tld(tld: str) -> bool:
    """Check if TLD is suspicious"""
    return tld.lower() in SUSPICIOUS_TLDS

def is_legitimate_tld(tld: str) -> bool:
    """Check if TLD is known legitimate"""
    return tld.lower() in LEGITIMATE_TLDS

def get_subdomain_count(url: str) -> int:
    """Count subdomains in URL"""
    domain = get_domain_from_url(url)
    if not domain:
        return 0
    
    # Don't count the main domain parts
    parts = domain.split('.')
    # If we have example.co.uk, that's 2 parts for main domain
    # If we have api.example.co.uk, that's 3 parts total
    if len(parts) > 2:
        return len(parts) - 2
    return 0

def get_domain_length(url: str) -> int:
    """Get domain name length (excluding TLD)"""
    domain = get_domain_from_url(url)
    if not domain:
        return 0
    
    parts = domain.split('.')
    if len(parts) >= 2:
        # Join all but last part (TLD)
        domain_name = '.'.join(parts[:-1])
        return len(domain_name)
    return len(domain)
