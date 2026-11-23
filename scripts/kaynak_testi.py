"""Görsel kaynaklarının GitHub Actions'tan erişilebilir olup olmadığını hızlıca sınar."""

import requests

UA = {"User-Agent": "DerinGizemVideoBot/1.0 (GitHub Actions; educational documentary)"}
TESTLER = {
    "commons": ("https://commons.wikimedia.org/w/api.php",
                {"action": "query", "format": "json", "titles": "File:Example.jpg", "prop": "imageinfo"}),
    "openverse": ("https://api.openverse.org/v1/images/", {"q": "mountain", "page_size": 1}),
    "nasa": ("https://images-api.nasa.gov/search", {"q": "aurora", "media_type": "image"}),
    "loc": ("https://www.loc.gov/photos/", {"q": "mountain", "fo": "json", "c": 1}),
    "natural-earth": ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/README.md", None),
}

for ad, (url, params) in TESTLER.items():
    try:
        y = requests.get(url, params=params, headers=UA, timeout=30)
        print(f"{ad:14s} {y.status_code} {y.headers.get('content-type', '')[:30]:30s} {y.text[:120]!r}")
    except Exception as hata:
        print(f"{ad:14s} HATA {hata}")
