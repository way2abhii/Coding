from bitlyshortener import Shortener


# Bitly Token (replace with your real token)
BITLY_TOKENS = ["ea039af98086dc4ee7998b9f4473aa9465d8046d"]

def shorten_url(url: str) -> str:
    try:
        shortener = Shortener(tokens=BITLY_TOKENS, max_cache_size=8192)
        return shortener.shorten_urls([url])[0]
    except Exception:
        # Fail-safe: return original link if Bitly fails
        return url

print(shorten_url("https://www.flipkart.com/noise-evolve-4-1-46-amoled-always-display-premium-design-bluetooth-calling-smartwatch/p/itm097197c3805ee?pid=SMWGTR2DVHHGA7HH&lid=LSTSMWGTR2DVHHGA7HHJFTVOS&marketplace=FLIPKART&cmpid=content_smartwatch_8965229628_gmc"))  # Example usage
