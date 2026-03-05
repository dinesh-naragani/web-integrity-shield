"""
Debug feature extraction to see what values are being extracted
"""

from comprehensive_feature_extractor import extract_comprehensive_features, get_feature_names

test_urls = [
    "https://www.chatgpt.com",
    "https://discord.com",
    "https://www.youtube.com",
    "https://paypa1.com",
    "http://192.168.1.1/login",
    "http://secure-login-paypal-verify.tk/account",
]

feature_names = get_feature_names()

print("\n" + "=" * 100)
print("FEATURE EXTRACTION DEBUG")
print("=" * 100)

for url in test_urls:
    print(f"\nURL: {url}")
    features, debug_info = extract_comprehensive_features(url)
    
    print("\nFeature Values:")
    for i, (name, value) in enumerate(zip(feature_names, features)):
        print(f"  {i+1:2d}. {name:35s} = {value:10.4f}")
    
    print("-" * 100)
