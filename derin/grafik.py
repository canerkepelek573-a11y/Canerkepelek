"""Kendi ürettiğimiz görseller: başlık/alıntı kartları, belge kartları ve haritalar.

Tamamen özgündür (lisans sorunu yok) ve kanalın görsel kimliğini taşır:
koyu zemin, tek sıcak vurgu rengi (turuncu-kırmızı), Inter yazı tipi.

    {kaynak: kart, baslik: "1 Şubat 1959", alt: "Kholat Syakhl yamacı", ust: "DOSYA #1"}
    {kaynak: kart, tur: belge, baslik: "CEZA DAVASI DOSYASI", satirlar: ["...", "..."]}
    {kaynak: harita, baslik: "Kuzey Urallar", alan: [55, 66, 56, 65],      # [batı, doğu, güney, kuzey]
     isaretler: [{ad: "Sverdlovsk", konum: [60.6, 56.84]}, ...], rota: true}
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTLAR = Path(__file__).resolve().parent.parent / "varliklar" / "fontlar"
SIYAH = (10, 11, 14)
KOYU = (20, 22, 28)
BEYAZ = (238, 236, 230)
GRI = (150, 150, 155)
VURGU = (232, 72, 38)        # turuncu-kırmızı marka rengi
KAGIT = (226, 214, 186)
MUREKKEP = (40, 36, 30)

NE_ULKELER = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
              "geojson/ne_50m_admin_0_countries.geojson")
NE_NEHIRLER = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
               "geojson/ne_10m_rivers_lake_centerlines.geojson")
ONBELLEK = Path(".onbellek/harita")


def buyuk(metin: str) -> str:
    """Türkçe büyük harf: i -> İ, ı -> I."""
    return metin.replace("i", "İ").replace("ı", "I").upper()


def font(ad: str, boyut: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTLAR / ad), boyut)


def mono(boyut: int) -> ImageFont.FreeTypeFont:
    for yol in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"):
        if Path(yol).exists():
            return ImageFont.truetype(yol, boyut)
    return font("Inter-Regular.otf", boyut)


def _sar(ciz: ImageDraw.ImageDraw, metin: str, f: ImageFont.FreeTypeFont, genislik: int) -> list[str]:
    satirlar, satir = [], ""
    for kelime in metin.split():
        aday = (satir + " " + kelime).strip()
        if ciz.textlength(aday, font=f) <= genislik:
            satir = aday
        else:
            if satir:
                satirlar.append(satir)
            satir = kelime
    if satir:
        satirlar.append(satir)
    return satirlar


def koyu_zemin(boyut: tuple[int, int], tohum: int = 0) -> Image.Image:
    """Hafif dokulu, kenarları kararan koyu zemin."""
    g, y = boyut
    rnd = random.Random(tohum)
    kucuk = Image.new("L", (g // 8, y // 8))
    kucuk.putdata([rnd.randint(0, 255) for _ in range((g // 8) * (y // 8))])
    doku = kucuk.resize(boyut, Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    zemin = Image.new("RGB", boyut, KOYU)
    zemin = Image.blend(zemin, Image.merge("RGB", [doku] * 3), 0.06)
    # vinyet
    maske = Image.new("L", boyut, 0)
    ImageDraw.Draw(maske).ellipse([-g * 0.25, -y * 0.35, g * 1.25, y * 1.35], fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(min(boyut) // 6))
    return Image.composite(zemin, Image.new("RGB", boyut, SIYAH), maske)


def baslik_karti(t: dict, boyut: tuple[int, int]) -> Image.Image:
    g, y = boyut
    olcek = min(g, y) / 1080
    im = koyu_zemin(boyut, tohum=len(t.get("baslik", "")))
    ciz = ImageDraw.Draw(im)
    fb = font("InterDisplay-Black.otf", int(110 * olcek))
    fa = font("Inter-SemiBold.otf", int(44 * olcek))
    fu = font("Inter-SemiBold.otf", int(30 * olcek))
    satirlar = _sar(ciz, t.get("baslik", ""), fb, int(g * 0.8))
    alt = _sar(ciz, t.get("alt", ""), fa, int(g * 0.75)) if t.get("alt") else []
    satir_y = int(fb.size * 1.15)
    toplam = len(satirlar) * satir_y + (len(alt) * int(fa.size * 1.4) + int(40 * olcek) if alt else 0)
    yy = (y - toplam) // 2
    if t.get("ust"):
        ust = buyuk(t["ust"])
        w = ciz.textlength(ust, font=fu)
        ciz.text(((g - w) / 2, yy - int(80 * olcek)), ust, font=fu, fill=VURGU)
    for s in satirlar:
        w = ciz.textlength(s, font=fb)
        ciz.text(((g - w) / 2, yy), s, font=fb, fill=BEYAZ)
        yy += satir_y
    if alt:
        yy += int(20 * olcek)
        ciz.line([(g / 2 - 60 * olcek, yy), (g / 2 + 60 * olcek, yy)], fill=VURGU, width=max(3, int(5 * olcek)))
        yy += int(30 * olcek)
        for s in alt:
            w = ciz.textlength(s, font=fa)
            ciz.text(((g - w) / 2, yy), s, font=fa, fill=GRI)
            yy += int(fa.size * 1.4)
    return im


def belge_karti(t: dict, boyut: tuple[int, int]) -> Image.Image:
    """Eski daktilo belgesi görünümünde kart (alıntı, tutanak, günlük satırları için)."""
    g, y = boyut
    olcek = min(g, y) / 1080
    im = koyu_zemin(boyut, tohum=7)
    kg = int(min(g * 0.62, y * 0.75 * 1.3))
    fb, fm = mono(int(40 * olcek)), mono(int(32 * olcek))
    olcum = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    ic = kg - int(140 * olcek)
    yukseklik = int(70 * olcek) + len(_sar(olcum, buyuk(t.get("baslik", "")), fb, ic)) * int(fb.size * 1.4) + int(25 * olcek)
    for satir in t.get("satirlar", []):
        yukseklik += len(_sar(olcum, satir, fm, ic)) * int(fm.size * 1.5) + int(fm.size * 0.6)
    yukseklik += int((200 if t.get("damga") else 90) * olcek)
    ky = min(int(y * 0.86), max(int(y * 0.45), yukseklik))
    kagit = Image.new("RGB", (kg, ky), KAGIT)
    rnd = random.Random(len(t.get("baslik", "")))
    piks = kagit.load()
    for _ in range(kg * ky // 40):
        x, yy = rnd.randrange(kg), rnd.randrange(ky)
        r, gg, b = piks[x, yy]
        d = rnd.randint(-18, 8)
        piks[x, yy] = (r + d, gg + d, b + d)
    ciz = ImageDraw.Draw(kagit)
    yy = int(70 * olcek)
    for s in _sar(ciz, buyuk(t.get("baslik", "")), fb, kg - int(140 * olcek)):
        ciz.text((int(70 * olcek), yy), s, font=fb, fill=MUREKKEP)
        yy += int(fb.size * 1.4)
    yy += int(25 * olcek)
    for satir in t.get("satirlar", []):
        for s in _sar(ciz, satir, fm, kg - int(140 * olcek)):
            ciz.text((int(70 * olcek), yy), s, font=fm, fill=MUREKKEP)
            yy += int(fm.size * 1.5)
        yy += int(fm.size * 0.6)
    if t.get("damga"):
        fd = font("InterDisplay-Black.otf", int(64 * olcek))
        damga = Image.new("RGBA", (int(ciz.textlength(t["damga"], font=fd)) + 40, fd.size + 40), (0, 0, 0, 0))
        dc = ImageDraw.Draw(damga)
        dc.rectangle([2, 2, damga.width - 3, damga.height - 3], outline=(170, 30, 30, 200), width=6)
        dc.text((20, 12), t["damga"], font=fd, fill=(170, 30, 30, 200))
        damga = damga.rotate(-12, expand=True)
        kagit.paste(damga, (kg - damga.width - int(50 * olcek), ky - damga.height - int(60 * olcek)), damga)
    kagit = kagit.convert("RGBA").rotate(rnd.uniform(-1.5, 1.5), expand=True, resample=Image.BICUBIC)
    golge = Image.new("RGBA", kagit.size, (0, 0, 0, 0))
    golge.putalpha(kagit.getchannel("A").point(lambda a: int(a * 0.6)))
    golge = golge.filter(ImageFilter.GaussianBlur(int(18 * olcek)))
    x0, y0 = (g - kagit.width) // 2, (y - kagit.height) // 2
    im.paste(golge, (x0 + int(14 * olcek), y0 + int(18 * olcek)), golge)
    im.paste(kagit, (x0, y0), kagit)
    return im


def _geojson(url: str) -> dict:
    ONBELLEK.mkdir(parents=True, exist_ok=True)
    yol = ONBELLEK / (hashlib.sha1(url.encode()).hexdigest()[:12] + ".geojson")
    if not yol.exists():
        yanit = requests.get(url, timeout=180)
        yanit.raise_for_status()
        yol.write_bytes(yanit.content)
    return json.loads(yol.read_text(encoding="utf-8"))


def _cizgiler(geometri: dict):
    t, k = geometri["type"], geometri["coordinates"]
    if t == "Polygon":
        yield from k
    elif t == "MultiPolygon":
        for p in k:
            yield from p
    elif t == "LineString":
        yield k
    elif t == "MultiLineString":
        yield from k


def harita(t: dict, boyut: tuple[int, int]) -> Image.Image:
    """Koyu, 'dosya' tarzı harita. Veri: Natural Earth (kamu malı)."""
    g, y = boyut
    olcek = min(g, y) / 1080
    bati, dogu, guney, kuzey = t["alan"]
    orta_enlem = math.radians((guney + kuzey) / 2)
    # alanı en-boy oranına sığdır (eşdikdörtgen projeksiyon, enlem düzeltmeli)
    gx, gy = (dogu - bati) * math.cos(orta_enlem), (kuzey - guney)
    if gx / gy > g / y:
        ek = (gx * y / g - gy) / 2
        guney, kuzey = guney - ek, kuzey + ek
    else:
        ek = (gy * g / y - gx) / 2 / math.cos(orta_enlem)
        bati, dogu = bati - ek, dogu + ek

    def p(lon: float, lat: float) -> tuple[float, float]:
        return (lon - bati) / (dogu - bati) * g, (kuzey - lat) / (kuzey - guney) * y

    im = koyu_zemin(boyut, tohum=3)
    ciz = ImageDraw.Draw(im, "RGBA")
    # enlem/boylam ızgarası
    adim = 1 if (kuzey - guney) < 12 else 5
    for lon in range(math.floor(bati), math.ceil(dogu) + 1):
        if lon % adim == 0:
            ciz.line([p(lon, guney), p(lon, kuzey)], fill=(255, 255, 255, 18), width=1)
    for lat in range(math.floor(guney), math.ceil(kuzey) + 1):
        if lat % adim == 0:
            ciz.line([p(bati, lat), p(dogu, lat)], fill=(255, 255, 255, 18), width=1)
    for ozellik in _geojson(NE_ULKELER)["features"]:
        for halka in _cizgiler(ozellik["geometry"]):
            ciz.line([p(*n) for n in halka], fill=(200, 200, 205, 110), width=max(2, int(2 * olcek)))
    if t.get("nehirler", True):
        for ozellik in _geojson(NE_NEHIRLER)["features"]:
            for cizgi in _cizgiler(ozellik["geometry"]):
                noktalar = [p(*n[:2]) for n in cizgi]
                if any(0 <= x <= g and 0 <= yy <= y for x, yy in noktalar):
                    ciz.line(noktalar, fill=(90, 130, 170, 120), width=max(1, int(2 * olcek)))

    fi = font("Inter-SemiBold.otf", int(34 * olcek))
    isaretler = t.get("isaretler", [])
    if t.get("rota") and len(isaretler) > 1:
        ciz.line([p(*i["konum"]) for i in isaretler], fill=VURGU + (200,), width=max(3, int(4 * olcek)), joint="curve")
    for i in isaretler:
        x, yy = p(*i["konum"])
        r = int((14 if i.get("ana") else 9) * olcek)
        ciz.ellipse([x - r, yy - r, x + r, yy + r], fill=VURGU if i.get("ana") else BEYAZ, outline=SIYAH, width=2)
        ciz.text((x + r + 10 * olcek, yy - fi.size * 0.6), i["ad"], font=fi, fill=BEYAZ,
                 stroke_width=max(2, int(3 * olcek)), stroke_fill=SIYAH)
    if t.get("baslik"):
        fb = font("InterDisplay-Black.otf", int(60 * olcek))
        ciz.text((int(60 * olcek), int(50 * olcek)), buyuk(t["baslik"]), font=fb, fill=BEYAZ)
        ciz.line([(int(60 * olcek), int(50 * olcek) + fb.size * 1.25),
                  (int(180 * olcek), int(50 * olcek) + fb.size * 1.25)], fill=VURGU, width=max(3, int(5 * olcek)))
    fk = font("Inter-Regular.otf", int(20 * olcek))
    ciz.text((int(20 * olcek), y - int(36 * olcek)), "Harita verisi: Natural Earth (kamu malı)", font=fk, fill=GRI)
    return im


def uret(t: dict, cikti: Path, boyut: tuple[int, int]) -> dict:
    cikti.mkdir(parents=True, exist_ok=True)
    anahtar = hashlib.sha1(json.dumps(t, sort_keys=True, ensure_ascii=False).encode() + str(boyut).encode()).hexdigest()[:12]
    yol = cikti / f"grafik_{anahtar}.png"
    if not yol.exists():
        if t["kaynak"] == "harita":
            im = harita(t, boyut)
        elif t.get("tur") == "belge":
            im = belge_karti(t, boyut)
        else:
            im = baslik_karti(t, boyut)
        im.save(yol)
    kaynak = "Natural Earth (kamu malı) verisiyle Gerçek Gizem" if t["kaynak"] == "harita" else "Gerçek Gizem"
    return {"yol": str(yol), "tur": "foto", "atif": f"Özgün grafik — {kaynak}", "grafik": True}
