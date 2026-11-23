"""Bir sitenin ana sayfası ve site haritasından, anahtar kelimeleri içeren sayfa adreslerini listeler."""

import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; GercekGizemResearch/1.0)"}
site, cikti = sys.argv[1], Path(sys.argv[2])
anahtarlar = sys.argv[3].split(",") if len(sys.argv) > 3 else []
adresler = set()
for yol in ("", "sitemap.xml", "sitemap_index.xml", "page-sitemap.xml", "post-sitemap.xml"):
    try:
        y = requests.get(urljoin(site, yol), headers=UA, timeout=60)
    except Exception:
        continue
    if not y.ok:
        continue
    for a in re.findall(r'(?:href=["\']|<loc>)([^"\'<]+)', y.text):
        tam = urljoin(site, a.strip())
        if tam.startswith(site):
            adresler.add(tam.split("#")[0])
secilen = sorted(a for a in adresler if not anahtarlar or any(k in a.lower() for k in anahtarlar))
cikti.parent.mkdir(parents=True, exist_ok=True)
cikti.write_text("\n".join(secilen) + "\n", encoding="utf-8")
print(f"{len(adresler)} adres, {len(secilen)} seçildi")
