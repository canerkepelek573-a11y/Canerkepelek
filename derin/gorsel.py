"""Senaryodaki görsel tanımlarını indirilmiş dosyalara çevirir ve lisanslarını kaydeder.

Yalnızca anahtar gerektirmeyen, telifsiz kaynaklar (CLAUDE.md §6):

    {kaynak: commons, dosya: "File:Ornek.jpg"}
    {kaynak: openverse, ara: "ural mountains winter", sira: 0}
    {kaynak: nasa, ara: "aurora", sira: 0}
    {kaynak: loc, ara: "soviet expedition 1950s", sira: 0}
    {kaynak: yerel, dosya: "varliklar/gorseller/x.jpg", lisans: "...", sahibi: "..."}
    {kaynak: kart, baslik: "1 Şubat 1959", alt: "Kholat Syakhl yamacı"}       # kendi ürettiğimiz kart
    {kaynak: harita, merkez: [59.45, 61.75], isaretler: [...], baslik: "..."}  # kendi ürettiğimiz harita

Her görsel için {"yol", "tur": "foto"|"video", "atif"} döner. Lisansı uygun olmayan
dosya kullanılmaz ve hata verilir (sessizce geçilmez).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import requests

ONBELLEK = Path(".onbellek/gorsel")
UA = {"User-Agent": "DerinGizemVideoBot/1.0 (GitHub Actions; educational documentary)"}

# Commons / Openverse için kabul edilen lisanslar (ticari kullanım + değiştirme serbest)
UYGUN_LISANSLAR = re.compile(
    r"^(public domain|pd|pd-.*|cc0|cc[- ]?zero|cc[- ]by(-sa)?([- ]\d\.\d)?.*|no restrictions)$", re.I
)
YASAK_LISANS = re.compile(r"\b(nc|nd|non-?commercial|no-?deriv|fair use|copyrighted)\b", re.I)


class LisansHatasi(RuntimeError):
    pass


def _dosya_adi(anahtar: str, uzanti: str) -> Path:
    ONBELLEK.mkdir(parents=True, exist_ok=True)
    return ONBELLEK / (hashlib.sha1(anahtar.encode()).hexdigest()[:16] + uzanti)


def _indir(url: str, hedef: Path) -> Path:
    if hedef.exists() and hedef.stat().st_size > 0:
        return hedef
    yanit = requests.get(url, headers=UA, timeout=120, stream=True)
    yanit.raise_for_status()
    with open(hedef, "wb") as f:
        for parca in yanit.iter_content(1 << 16):
            f.write(parca)
    return hedef


def _json(url: str, params: dict | None = None, deneme_sayisi: int = 5) -> dict:
    """GET + JSON; geçici hatalarda (429, 5xx, ağ) bekleyip yeniden dener, sonunda açık hata verir."""
    import time

    son = ""
    for deneme in range(deneme_sayisi):
        try:
            yanit = requests.get(url, params=params, headers=UA, timeout=60)
        except requests.RequestException as hata:
            son = f"{type(hata).__name__}"
        else:
            if yanit.ok:
                try:
                    return yanit.json()
                except ValueError:
                    son = f"JSON değil: {yanit.text[:120]!r}"
            else:
                son = f"HTTP {yanit.status_code}"
                if yanit.status_code < 500 and yanit.status_code != 429:
                    break
        time.sleep(3 * (deneme + 1))
    raise RuntimeError(f"{url} cevap vermedi: {son}")


def _lisans_kontrol(lisans: str, kaynak: str) -> None:
    temiz = (lisans or "").strip()
    if not temiz or YASAK_LISANS.search(temiz) or not UYGUN_LISANSLAR.match(temiz):
        raise LisansHatasi(f"Uygun olmayan lisans '{lisans}' — {kaynak}")


def _html_temizle(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def commons(dosya: str) -> dict:
    baslik = dosya if dosya.startswith("File:") else f"File:{dosya}"
    yanit = _json(
        "https://commons.wikimedia.org/w/api.php",
        {
            "action": "query", "format": "json", "titles": baslik, "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime", "iiurlwidth": 3840,
        },
    )
    sayfa = next(iter(yanit["query"]["pages"].values()))
    if "imageinfo" not in sayfa:
        raise FileNotFoundError(f"Commons'ta bulunamadı: {baslik}")
    bilgi = sayfa["imageinfo"][0]
    meta = bilgi.get("extmetadata", {})
    lisans = meta.get("LicenseShortName", {}).get("value", "")
    _lisans_kontrol(lisans, baslik)
    video = bilgi.get("mime", "").startswith("video/")
    url = bilgi["url"] if video else bilgi.get("thumburl") or bilgi["url"]
    uzanti = Path(url.split("?")[0]).suffix or (".webm" if video else ".jpg")
    yol = _indir(url, _dosya_adi(url, uzanti))
    sahibi = _html_temizle(meta.get("Artist", {}).get("value", "")) or "Bilinmiyor"
    return {
        "yol": str(yol), "tur": "video" if video else "foto",
        "atif": f"{baslik.removeprefix('File:')} — {sahibi} — {lisans} — Wikimedia Commons "
                f"(https://commons.wikimedia.org/wiki/{baslik.replace(' ', '_')})",
    }


def commons_ara(ara: str, sira: int = 0) -> dict:
    """Commons'ta arama yapar; yalnızca uygun lisanslı ve yeterince büyük fotoğrafları kabul eder."""
    veri = _json("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{ara} filetype:bitmap", "gsrlimit": 30, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 3840,
    })
    uygun = []
    for sayfa in sorted(veri.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        bilgi = (sayfa.get("imageinfo") or [{}])[0]
        lisans = bilgi.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        try:
            _lisans_kontrol(lisans, sayfa["title"])
        except LisansHatasi:
            continue
        if (bilgi.get("width") or 0) >= 1200:
            uygun.append(sayfa["title"])
    if len(uygun) <= sira:
        raise FileNotFoundError(f"Commons aramasında uygun sonuç yok: '{ara}'")
    return commons(uygun[sira])


def openverse(ara: str, sira: int = 0, yon: str | None = None) -> dict:
    params = {"q": ara, "license_type": "commercial,modification", "page_size": 20, "mature": "false"}
    if yon:
        params["aspect_ratio"] = {"yatay": "wide", "dikey": "tall"}.get(yon, yon)
    sonuclar = _json("https://api.openverse.org/v1/images/", params)
    sonuclar = [r for r in sonuclar.get("results", []) if (r.get("width") or 0) >= 1200]
    if len(sonuclar) <= sira:
        raise FileNotFoundError(f"Openverse'te yeterli sonuç yok: '{ara}' (sıra {sira})")
    r = sonuclar[sira]
    lisans = f"CC {r['license'].upper()} {r.get('license_version', '')}".strip()
    if r["license"] in ("cc0", "pdm"):
        lisans = "CC0" if r["license"] == "cc0" else "Public domain"
    _lisans_kontrol(lisans, r.get("foreign_landing_url", ""))
    yol = _indir(r["url"], _dosya_adi(r["url"], Path(r["url"].split("?")[0]).suffix or ".jpg"))
    return {
        "yol": str(yol), "tur": "foto",
        "atif": f"{r.get('title') or 'Fotoğraf'} — {r.get('creator') or 'Bilinmiyor'} — {lisans} — "
                f"{r.get('foreign_landing_url')}",
    }


def nasa(ara: str, sira: int = 0) -> dict:
    veri = _json("https://images-api.nasa.gov/search", {"q": ara, "media_type": "image"})
    ogeler = veri["collection"]["items"]
    if len(ogeler) <= sira:
        raise FileNotFoundError(f"NASA arşivinde sonuç yok: '{ara}'")
    oge = ogeler[sira]
    nasa_id = oge["data"][0]["nasa_id"]
    dosyalar = _json(oge["href"])
    url = next((u for u in dosyalar if re.search(r"~(orig|large)\.jpg$", u)), dosyalar[0])
    yol = _indir(url, _dosya_adi(url, ".jpg"))
    return {"yol": str(yol), "tur": "foto",
            "atif": f"{oge['data'][0].get('title')} — NASA — Kamu malı (https://images.nasa.gov/details/{nasa_id})"}


def loc(ara: str, sira: int = 0) -> dict:
    veri = _json("https://www.loc.gov/photos/", {"q": ara, "fo": "json", "c": 25, "fa": "online-format:image"})
    uygun = [r for r in veri.get("results", []) if "no known restrictions" in json.dumps(r.get("rights", "")).lower()
             or "no known restrictions" in json.dumps(r).lower()]
    if len(uygun) <= sira:
        raise FileNotFoundError(f"Library of Congress'te kısıtlamasız sonuç yok: '{ara}'")
    r = uygun[sira]
    url = (r.get("image_url") or [None])[-1]
    if not url:
        raise FileNotFoundError(f"Library of Congress görsel adresi yok: {r.get('id')}")
    url = url.split("#")[0]
    yol = _indir(url, _dosya_adi(url, ".jpg"))
    return {"yol": str(yol), "tur": "foto",
            "atif": f"{r.get('title')} — Library of Congress — No known restrictions ({r.get('id')})"}


def yerel(dosya: str, lisans: str, sahibi: str = "Derin Gizem") -> dict:
    yol = Path(dosya)
    if not yol.exists():
        raise FileNotFoundError(dosya)
    tur = "video" if yol.suffix.lower() in (".mp4", ".webm", ".mov") else "foto"
    return {"yol": str(yol), "tur": tur, "atif": f"{yol.name} — {sahibi} — {lisans}"}


def coz(tanim: dict, cikti: Path, boyut: tuple[int, int]) -> dict:
    """Bir görsel tanımını yerel dosyaya çevirir."""
    k = tanim["kaynak"]
    if k == "commons":
        return commons(tanim["dosya"])
    if k == "openverse":
        try:
            return openverse(tanim["ara"], tanim.get("sira", 0), tanim.get("yon"))
        except Exception as hata:          # Openverse geçici olarak cevap vermezse Commons'ta ara
            print(f"Openverse başarısız ({hata}); Commons'ta aranıyor: {tanim['ara']}")
            return commons_ara(tanim["ara"], tanim.get("sira", 0))
    if k == "commons_ara":
        return commons_ara(tanim["ara"], tanim.get("sira", 0))
    if k == "nasa":
        return nasa(tanim["ara"], tanim.get("sira", 0))
    if k == "loc":
        return loc(tanim["ara"], tanim.get("sira", 0))
    if k == "yerel":
        return yerel(tanim["dosya"], tanim.get("lisans", "Derin Gizem özgün içerik"), tanim.get("sahibi", "Derin Gizem"))
    if k in ("kart", "harita"):
        from derin import grafik
        return grafik.uret(tanim, cikti, boyut)
    raise ValueError(f"Bilinmeyen görsel kaynağı: {k}")
