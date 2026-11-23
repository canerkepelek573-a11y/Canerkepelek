"""Görsel aday tabloları: her arama için lisansı uygun adayları küçük resimlerle bir tabloya dizer.

Amaç: fotoğrafları otomatik değil, bakarak seçmek (CLAUDE.md §3.1 içerik uyumu).
Girdi : bolumler/<bolum>/aday_aramalari.yaml   →  {ad: "arama terimi", ...}
Çıktı : bolumler/<bolum>/adaylar/<ad>.jpg      (numaralı küçük resimler)
        bolumler/<bolum>/adaylar/adaylar.json  (numara → senaryoya yazılacak görsel tanımı)

Kullanım: python scripts/gorsel_adaylari.py bolumler/001-dyatlov
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from derin.gorsel import UA, LisansHatasi, _json, _lisans_kontrol  # noqa: E402
from derin.grafik import font  # noqa: E402

KUCUK = (360, 220)
SUTUN = 4


def openverse_adaylar(ara: str, adet: int = 8) -> list[dict]:
    veri = _json("https://api.openverse.org/v1/images/", {
        "q": ara, "license_type": "commercial,modification", "page_size": adet, "mature": "false"})
    sonuc = []
    for r in veri.get("results", []):
        if (r.get("width") or 1600) < 1000:
            continue
        sonuc.append({"tanim": {"kaynak": "openverse", "id": r["id"]}, "kucuk": r.get("thumbnail"),
                      "baslik": r.get("title") or "", "lisans": f"{r['license']} {r.get('license_version', '')}",
                      "boyut": f"{r.get('width')}x{r.get('height')}"})
    return sonuc


def commons_adaylar(ara: str, adet: int = 8) -> list[dict]:
    veri = _json("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{ara} filetype:bitmap", "gsrlimit": 20, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 330})
    sonuc = []
    for sayfa in sorted(veri.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        bilgi = (sayfa.get("imageinfo") or [{}])[0]
        lisans = bilgi.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        try:
            _lisans_kontrol(lisans, sayfa["title"])
        except LisansHatasi:
            continue
        if (bilgi.get("width") or 0) < 1200:
            continue
        sonuc.append({"tanim": {"kaynak": "commons", "dosya": sayfa["title"]}, "kucuk": bilgi.get("thumburl"),
                      "baslik": sayfa["title"].removeprefix("File:"), "lisans": lisans,
                      "boyut": f"{bilgi.get('width')}x{bilgi.get('height')}"})
        if len(sonuc) >= adet:
            break
    return sonuc


def kucuk_resim(url: str | None) -> Image.Image:
    bos = Image.new("RGB", KUCUK, (40, 40, 45))
    if not url:
        return bos
    for deneme in range(4):
        try:
            if "wikimedia" in url:
                time.sleep(2)
            y = requests.get(url, headers=UA, timeout=40)
            if y.status_code == 429:
                time.sleep(20 * (deneme + 1))
                continue
            y.raise_for_status()
            im = Image.open(io.BytesIO(y.content)).convert("RGB")
            im.thumbnail(KUCUK)
            zemin = bos.copy()
            zemin.paste(im, ((KUCUK[0] - im.width) // 2, (KUCUK[1] - im.height) // 2))
            return zemin
        except Exception:
            time.sleep(3)
    return bos


def tablo(ad: str, ara: str, adaylar: list[dict], hedef: Path) -> None:
    satir = max(1, (len(adaylar) + SUTUN - 1) // SUTUN)
    hucre_y = KUCUK[1] + 46
    im = Image.new("RGB", (SUTUN * (KUCUK[0] + 10) + 10, 60 + satir * (hucre_y + 10)), (15, 15, 18))
    ciz = ImageDraw.Draw(im)
    ciz.text((12, 14), f"{ad}  —  \"{ara}\"", font=font("Inter-SemiBold.otf", 26), fill=(240, 240, 240))
    fk, fn = font("Inter-Regular.otf", 15), font("InterDisplay-Black.otf", 30)
    for i, a in enumerate(adaylar):
        x = 10 + (i % SUTUN) * (KUCUK[0] + 10)
        y = 60 + (i // SUTUN) * (hucre_y + 10)
        im.paste(kucuk_resim(a["kucuk"]), (x, y))
        ciz.rectangle([x, y, x + 44, y + 40], fill=(232, 72, 38))
        ciz.text((x + 8, y + 2), str(i), font=fn, fill=(255, 255, 255))
        kaynak = "OV" if a["tanim"]["kaynak"] == "openverse" else "WC"
        ciz.text((x, y + KUCUK[1] + 4), f"{kaynak} · {a['lisans'][:18]} · {a['boyut']}", font=fk, fill=(200, 200, 200))
        ciz.text((x, y + KUCUK[1] + 24), a["baslik"][:46], font=fk, fill=(150, 150, 150))
    im.save(hedef, quality=85)


def main() -> int:
    bolum = Path(sys.argv[1])
    aramalar = yaml.safe_load((bolum / "aday_aramalari.yaml").read_text(encoding="utf-8"))
    klasor = bolum / "adaylar"
    klasor.mkdir(exist_ok=True)
    hepsi = {}
    for ad, ara in aramalar.items():
        adaylar = []
        for kaynak in (commons_adaylar, openverse_adaylar):
            try:
                adaylar += kaynak(ara)
            except Exception as hata:
                print(f"{ad}: {kaynak.__name__} başarısız: {hata}")
        tablo(ad, ara, adaylar, klasor / f"{ad}.jpg")
        hepsi[ad] = {"ara": ara, "adaylar": [{"no": i, **a["tanim"], "baslik": a["baslik"], "lisans": a["lisans"]}
                                            for i, a in enumerate(adaylar)]}
        print(f"{ad}: {len(adaylar)} aday")
    (klasor / "adaylar.json").write_text(json.dumps(hepsi, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
