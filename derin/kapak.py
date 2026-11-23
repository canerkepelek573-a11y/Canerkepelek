"""YouTube kapak fotoğrafı (1280x720).

Araştırmaya göre (docs/arastirma-youtube.md): tek odak nesne, 2–4 kelime büyük yazı,
koyu zemin + tek vurgu rengi, köşede sabit "GERÇEK GİZEM · DOSYA #N" rozeti.

    kapak:
      gorsel: {kaynak: commons, dosya: "File:..."}
      metin: "ÇADIR İÇERİDEN|KESİLMİŞTİ"     # '|' satır böler; ikinci satır vurgu renginde
      odak: sag                              # görselin hangi yarısı görünsün: sol / sag / orta
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from derin import gorsel
from derin.grafik import BEYAZ, SIYAH, VURGU, buyuk, font

BOYUT = (1280, 720)


def olustur(tanim: dict, bolum_no: int, hedef: Path, marka: str = "Gerçek Gizem") -> Path:
    g, y = BOYUT
    try:
        kaynak = gorsel.coz(tanim["gorsel"], hedef.parent, BOYUT)
    except Exception as hata:   # görsel alınamazsa koyu zeminle devam et ve bildir
        print(f"UYARI: kapak görseli alınamadı: {hata}")
        kaynak = gorsel.coz({"kaynak": "kart", "baslik": ""}, hedef.parent, BOYUT)
    im = Image.open(kaynak["yol"]).convert("RGB")
    odak = {"sol": (0.0, 0.5), "sag": (1.0, 0.5)}.get(tanim.get("odak", "orta"), (0.5, 0.5))
    im = ImageOps.fit(im, BOYUT, Image.LANCZOS, centering=odak)
    im = ImageEnhance.Color(im).enhance(0.75)
    im = ImageEnhance.Contrast(im).enhance(1.15)
    im = ImageEnhance.Brightness(im).enhance(0.8)

    # yazının okunması için soldan sağa kararan geçiş + kenar vinyeti
    gecis = Image.new("L", BOYUT)
    ciz = ImageDraw.Draw(gecis)
    for x in range(g):
        ciz.line([(x, 0), (x, y)], fill=int(235 * max(0.0, 1 - x / (g * 0.68)) ** 1.3))
    im = Image.composite(Image.new("RGB", BOYUT, SIYAH), im, gecis)
    vinyet = Image.new("L", BOYUT, 0)
    ImageDraw.Draw(vinyet).ellipse([-g * 0.2, -y * 0.3, g * 1.2, y * 1.3], fill=255)
    im = Image.composite(im, Image.new("RGB", BOYUT, SIYAH), vinyet.filter(ImageFilter.GaussianBlur(120)))

    ciz = ImageDraw.Draw(im)
    satirlar = [buyuk(s.strip()) for s in tanim["metin"].split("|")]
    boy = 118 if max(len(s) for s in satirlar) <= 12 else 96
    f = font("InterDisplay-Black.otf", boy)
    while max(ciz.textlength(s, font=f) for s in satirlar) > g * 0.62 and boy > 60:
        boy -= 4
        f = font("InterDisplay-Black.otf", boy)
    yy = (y - len(satirlar) * boy * 1.08) / 2 + 20
    for i, s in enumerate(satirlar):
        renk = VURGU if i == len(satirlar) - 1 and len(satirlar) > 1 else BEYAZ
        ciz.text((64, yy), s, font=f, fill=renk, stroke_width=4, stroke_fill=SIYAH)
        yy += boy * 1.08

    rozet = f"{buyuk(marka)} · DOSYA #{bolum_no}"
    fr = font("Inter-Black.otf", 30)
    w = ciz.textlength(rozet, font=fr)
    ciz.rectangle([48, 40, 48 + w + 36, 40 + 52], fill=VURGU)
    ciz.text((66, 48), rozet, font=fr, fill=BEYAZ)

    hedef.parent.mkdir(parents=True, exist_ok=True)
    im.save(hedef, quality=92)
    return hedef
