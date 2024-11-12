import logging
from urllib.parse import urlparse, quote
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def sanitize_url(url: str) -> str:
    return quote(url, safe=":/")


def is_safe_scheme(url: str) -> bool:
    # Limit URLs to HTTPS to avoid vulnerabilities associated with other schemes:
    return urlparse(url).scheme in ["https"]


def sanitize_url(url: str) -> str:
    return quote(url, safe=":/")


def is_valid_url(url: str) -> bool:
    try:
        parsed_url = urlparse(url)
        # Requires scheme and domain
        return all([parsed_url.scheme, parsed_url.netloc])
    except Exception:
        return False


def check_google_safe_browsing(api_key: str, url: str) -> bool:
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    payload = {
        "client": {"clientId": "yourcompanyname", "clientVersion": "1.5.2"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    params = {"key": api_key}
    response = requests.post(endpoint, json=payload, params=params)
    result = response.json()
    return "matches" not in result


def is_safe_url(url: str, api_key: str = None) -> bool:
    if not is_valid_url(url):
        return False
    if not is_safe_scheme(url):
        return False
    if api_key and not check_google_safe_browsing(api_key, url):
        return False
    return True


def identify_platform(url: str) -> str:
    if "flipkart.com" in url:
        return "flipkart"
    elif "amazon.com" in url:
        return "amazon"
    else:
        logger.error(f"Unsupported platform URL: {url}")
        raise ValueError("Unsupported platform URL")
