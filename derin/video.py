"""Zaman çizelgesi + görseller + ses → bitmiş video (ana video 16:9 veya Shorts 9:16).

Ses–görüntü uyumu (CLAUDE.md §3.1):
- Görüntü geçişleri yalnızca cümle sınırlarında yapılır; süreler ölçülmüş ses zamanlarından gelir.
- Altyazılar kelime kelime, sesin okunduğu anda gösterilir.
- Müzik ve ses efekti yoktur; videonun tek sesi anlatıcıdır.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from derin import gorsel, grafik

FPS = 30
FONTLAR = Path(__file__).resolve().parent.parent / "varliklar" / "fontlar"

BICIMLER = {
    "ana": {"boyut": (1920, 1080)},
    "shorts": {"boyut": (1080, 1920)},
}


@dataclass
class Sahne:
    gorsel: dict
    baslangic: float
    bitis: float
    sira: int


# ----------------------------------------------------------------------------- sahne planı

def _kesim_noktalari(p: dict, n: int) -> list[float]:
    """Paragrafı n görsele böler; kesimler cümle sınırlarına (gerekirse kelime aralarına) oturur."""
    bas, bit = p["baslangic"], p["bitis"]
    if n <= 1:
        return [bas]
    adaylar = [c["baslangic"] for c in p["cumleler"][1:]]
    if len(adaylar) < n - 1:
        # yeterli cümle yoksa virgülden sonraki kelime başlarını da aday yap
        adaylar += [t[1] for i, t in enumerate(p["goster"][1:], 1) if p["goster"][i - 1][0].endswith((",", ";", ":"))]
    if len(adaylar) < n - 1:
        adaylar += [t[1] for t in p["goster"][1:]]
    adaylar = sorted(set(adaylar))
    kesimler = [bas]
    for k in range(1, n):
        hedef = bas + (bit - bas) * k / n
        uygun = [a for a in adaylar if a > kesimler[-1] + 1.5]
        if not uygun:
            break
        kesimler.append(min(uygun, key=lambda a: abs(a - hedef)))
    return kesimler


def sahne_plani(zaman: dict, cozulmus: dict[int, list[dict]], toplam: float) -> list[Sahne]:
    sahneler: list[Sahne] = []
    for p in zaman["paragraflar"]:
        gorseller = cozulmus.get(p["sira"], [])
        if not gorseller:
            continue
        kesimler = _kesim_noktalari(p, len(gorseller))
        for g, k in zip(gorseller, kesimler):
            baslangic = 0.0 if not sahneler else k
            if sahneler:
                sahneler[-1].bitis = baslangic
            sahneler.append(Sahne(g, baslangic, toplam, len(sahneler)))
    if not sahneler:
        raise RuntimeError("Hiç görsel çözülemedi")
    return [s for s in sahneler if s.bitis - s.baslangic > 0.05]


# ----------------------------------------------------------------------------- sahne klipleri

def _hareket(sira: int, kare: int, grafik_mi: bool) -> tuple[str, str, str]:
    """Ken Burns hareketi: yakınlaşma / uzaklaşma / sola / sağa kaydırma (sırayla değişir)."""
    hiz = 0.06 if grafik_mi else 0.12            # toplam yakınlaşma oranı
    adim = hiz / max(kare, 1)
    tur = sira % 4
    if tur == 0:
        return f"1+{adim}*on", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if tur == 1:
        return f"{1 + hiz}-{adim}*on", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if tur == 2:
        return f"{1 + hiz}", f"(iw-iw/zoom)*on/{max(kare, 1)}", "ih/2-(ih/zoom/2)"
    return f"{1 + hiz}", f"(iw-iw/zoom)*(1-on/{max(kare, 1)})", "ih/2-(ih/zoom/2)"


def klip(sahne: Sahne, boyut: tuple[int, int], hedef: Path) -> Path:
    g, y = boyut
    bas_kare, bit_kare = round(sahne.baslangic * FPS), round(sahne.bitis * FPS)
    kare = max(1, bit_kare - bas_kare)
    sure = kare / FPS
    kaynak = sahne.gorsel["yol"]
    ton = "eq=brightness=-0.03:saturation=0.82:contrast=1.05"
    if sahne.gorsel["tur"] == "video":
        vf = (f"scale={g}:{y}:force_original_aspect_ratio=increase,crop={g}:{y},fps={FPS},"
              f"{ton},format=yuv420p")
        komut = ["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", kaynak, "-an",
                 "-vf", vf, "-frames:v", str(kare)]
    else:
        z, x, yy = _hareket(sahne.sira, kare, sahne.gorsel.get("grafik", False))
        on_olcek = f"scale={2 * g}:{2 * y}:force_original_aspect_ratio=increase,crop={2 * g}:{2 * y}"
        if not sahne.gorsel.get("grafik"):
            # dikey formata yatay fotoğraf gelirse kenarları bulanık zeminle doldur
            on_olcek = (f"split[a][b];[a]scale={2 * g}:{2 * y}:force_original_aspect_ratio=increase,"
                        f"crop={2 * g}:{2 * y},boxblur=40:5[z];[b]scale={2 * g}:{2 * y}:"
                        f"force_original_aspect_ratio=decrease[o];[z][o]overlay=(W-w)/2:(H-h)/2")
            if g > y or not sahne.gorsel.get("sigdir"):   # varsayılan: fotoğraf ekranı doldursun
                on_olcek = f"scale={2 * g}:{2 * y}:force_original_aspect_ratio=increase,crop={2 * g}:{2 * y}"
        vf = (f"{on_olcek},zoompan=z='{z}':x='{x}':y='{yy}':d={kare}:s={g}x{y}:fps={FPS},"
              f"{ton},format=yuv420p")
        komut = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", kaynak, "-filter_complex", vf,
                 "-frames:v", str(kare)]
    komut += ["-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(hedef)]
    subprocess.run(komut, check=True)
    return hedef


# ----------------------------------------------------------------------------- ASS (yazılar)

def _ass_zaman(t: float) -> str:
    t = max(0.0, t)
    s, cs = divmod(round(t * 100), 100)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _kac(metin: str) -> str:
    return metin.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def _altyazi_parcalari(zaman: dict, en_fazla_karakter: int, en_fazla_kelime: int) -> list[tuple[float, float, list]]:
    parcalar = []
    for p in zaman["paragraflar"]:
        parca: list = []
        for tok in p["goster"]:
            uzun = len(" ".join(t[0] for t in parca + [tok])) > en_fazla_karakter or len(parca) >= en_fazla_kelime
            if parca and uzun:
                parcalar.append(parca)
                parca = []
            parca.append(tok)
            if tok[0].endswith((".", "!", "?", "…", ":")) or (tok[0].endswith(",") and len(parca) >= 3):
                parcalar.append(parca)
                parca = []
        if parca:
            parcalar.append(parca)
    sonuc = []
    for i, parca in enumerate(parcalar):
        bas, bit = parca[0][1], parca[-1][2]
        sonraki = parcalar[i + 1][0][1] if i + 1 < len(parcalar) else bit + 0.5
        if sonraki - bit < 0.6:          # kısa boşlukta yazıyı bir sonrakine kadar tut (titremesin)
            bit = sonraki
        sonuc.append((bas, bit, parca))
    return sonuc


def ass_dosyasi(zaman: dict, bicim: str, boyut: tuple[int, int], marka: str, hedef: Path,
                son_kart: tuple[float, float] | None = None) -> Path:
    g, y = boyut
    shorts = bicim == "shorts"
    alt_boyut, alt_font = (82, "Inter Display Black") if shorts else (50, "Inter SemiBold")
    stiller = [
        f"Style: Altyazi,{alt_font},{alt_boyut},&H00F0F0F0,&H00F0F0F0,&H00000000,&H96000000,"
        f"0,0,0,0,100,100,0,0,1,{6 if shorts else 3},{2 if shorts else 1},{5 if shorts else 2},80,80,"
        f"{0 if shorts else 64},1",
        "Style: Baslik,Inter Display Black,96,&H00F0F0F0,&H00F0F0F0,&H00000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,0,0,5,120,120,0,1",
        "Style: Ust,Inter SemiBold,34,&H002648E8,&H002648E8,&H00000000,&H00000000,"
        "0,0,0,0,100,100,3,0,1,0,0,5,120,120,0,1",
        "Style: AltBilgi,Inter SemiBold,40,&H00F0F0F0,&H00F0F0F0,&H00000000,&HA0141210,"
        "0,0,0,0,100,100,1,0,3,14,0,1,90,90,170,1",
        "Style: Abone,Inter Display Black,46,&H00FFFFFF,&H00FFFFFF,&H001010C8,&H001010C8,"
        "0,0,0,0,100,100,2,0,3,18,0,5,0,0,0,1",
        "Style: AboneUst,Inter SemiBold,30,&H00F0F0F0,&H00F0F0F0,&H00000000,&H64000000,"
        "0,0,0,0,100,100,1,0,1,2,0,5,0,0,0,1",
        "Style: Marka,Inter Display Black,30,&H50F0F0F0,&H50F0F0F0,&H00000000,&H00000000,"
        "0,0,0,0,100,100,4,0,1,0,0,7,48,48,40,1",
        "Style: Perde,Inter SemiBold,10,&H78000000,&H78000000,&H00000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
    ]
    olaylar: list[str] = []

    def olay(stil: str, bas: float, bit: float, metin: str, katman: int = 0) -> None:
        olaylar.append(f"Dialogue: {katman},{_ass_zaman(bas)},{_ass_zaman(bit)},{stil},,0,0,0,,{metin}")

    toplam = zaman["sure"]
    # Marka (köşede sabit)
    olay("Marka", 0, toplam, grafik.buyuk(marka), 1)

    # Altyazılar
    if shorts:
        for bas, bit, parca in _altyazi_parcalari(zaman, 18, 3):
            for i, tok in enumerate(parca):
                kelime_bas = bas if i == 0 else tok[1]
                kelime_bit = parca[i + 1][1] if i + 1 < len(parca) else bit
                metin = " ".join(
                    ("{\\c&H002648E8&}" + _kac(t[0]) + "{\\c&H00F0F0F0&}") if j == i else _kac(t[0])
                    for j, t in enumerate(parca)
                )
                olay("Altyazi", kelime_bas, kelime_bit, "{\\pos(%d,%d)}%s" % (g // 2, int(y * 0.66), metin), 2)
    else:
        for bas, bit, parca in _altyazi_parcalari(zaman, 46, 9):
            olay("Altyazi", bas, bit, _kac(" ".join(t[0] for t in parca)), 2)

    # Bölüm başlıkları, alt bilgi yazıları, abone çağrıları
    perde = f"{{\\p1\\fad(300,400)}}m 0 0 l {g} 0 {g} {y} 0 {y}"
    bolum_no = 0
    for p in zaman["paragraflar"]:
        if p.get("bolum") and not shorts and p["sira"] > 0:
            bolum_no += 1
            bas = p["baslangic"] - 0.9
            bit = bas + 4.2
            olay("Perde", bas, bit, perde, 3)
            olay("Ust", bas, bit, "{\\fad(300,400)\\pos(%d,%d)}BÖLÜM %d" % (g // 2, y // 2 - 95, bolum_no + 1), 4)
            olay("Baslik", bas, bit, "{\\fad(300,400)\\pos(%d,%d)}%s" % (g // 2, y // 2 + 10, _kac(p["bolum"])), 4)
        if p.get("yazi"):
            bas = p["baslangic"] + 0.3
            konum = "\\an8\\pos(%d,%d)" % (g // 2, int(y * 0.24)) if shorts else ""
            olay("AltBilgi", bas, bas + 5.0, "{\\fad(250,350)" + konum + "}" + _kac(p["yazi"]), 4)
        if p.get("abone"):
            bas = p["baslangic"] + 0.6
            bit = bas + 4.0
            x, yy = (g // 2, int(y * 0.16)) if shorts else (g - 230, 120)
            animasyon = "{\\fad(200,300)\\fscx70\\fscy70\\t(0,250,\\fscx105\\fscy105)\\t(250,400,\\fscx100\\fscy100)"
            olay("Abone", bas, bit, animasyon + "\\pos(%d,%d)}ABONE OL" % (x, yy), 5)
            olay("AboneUst", bas, bit, "{\\fad(200,300)\\pos(%d,%d)}Dosyanın devamı için" % (x, yy - 62), 5)

    if son_kart:
        bas, bit = son_kart
        olay("Ust", bas, bit, "{\\fad(400,0)\\pos(%d,%d)}%s" % (g // 2, int(y * 0.22), grafik.buyuk(marka)), 4)

    baslik = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {g}\nPlayResY: {y}\nWrapStyle: 0\n"
              "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
              "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
              "Alignment, MarginL, MarginR, MarginV, Encoding\n")
    govde = "\n".join(stiller) + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    hedef.write_text(baslik + govde + "\n".join(olaylar) + "\n", encoding="utf-8")
    return hedef


def srt_dosyasi(zaman: dict, hedef: Path) -> Path:
    """YouTube'a ayrıca yüklenecek altyazı (CC) dosyası."""
    def z(t: float) -> str:
        ms = round(t * 1000)
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    satirlar = []
    for i, (bas, bit, parca) in enumerate(_altyazi_parcalari(zaman, 46, 9), 1):
        satirlar.append(f"{i}\n{z(bas)} --> {z(bit)}\n{' '.join(t[0] for t in parca)}\n")
    hedef.write_text("\n".join(satirlar), encoding="utf-8")
    return hedef


# ----------------------------------------------------------------------------- ana akış

def olustur(zaman: dict, ses: Path, bicim: str, klasor: Path, marka: str = "Gerçek Gizem",
            son_kart_sure: float = 0.0, son_kart: dict | None = None) -> dict:
    """Videoyu üretir; klasor/video.mp4, klasor/altyazi.srt ve klasor/kaynaklar.txt yazar."""
    boyut = BICIMLER[bicim]["boyut"]
    klasor.mkdir(parents=True, exist_ok=True)
    gecici = klasor / "gecici"
    gecici.mkdir(exist_ok=True)

    uyarilar: list[str] = []
    atiflar: list[str] = []
    cozulmus: dict[int, list[dict]] = {}
    for p in zaman["paragraflar"]:
        for tanim in p.get("gorseller", []):
            try:
                g = gorsel.coz(tanim, gecici, boyut)
                g["sigdir"] = tanim.get("sigdir", False)
            except Exception as hata:
                uyarilar.append(f"Paragraf {p['sira']}: görsel alınamadı ({tanim}): {hata}")
                continue
            cozulmus.setdefault(p["sira"], []).append(g)
            if g["atif"] not in atiflar:
                atiflar.append(g["atif"])

    toplam = zaman["sure"] + son_kart_sure
    sahneler = sahne_plani(zaman, cozulmus, zaman["sure"])
    if son_kart_sure > 0:
        kart = grafik.uret(son_kart or {"kaynak": "kart", "baslik": "Bir sonraki dosyada görüşmek üzere",
                                        "alt": "Abone olmayı unutmayın"}, gecici, boyut)
        sahneler[-1].bitis = zaman["sure"]
        sahneler.append(Sahne(kart, zaman["sure"], toplam, len(sahneler)))

    with ThreadPoolExecutor(max_workers=max(1, (os.cpu_count() or 2))) as havuz:
        klipler = list(havuz.map(lambda s: klip(s, boyut, gecici / f"sahne_{s.sira:04d}.mp4"), sahneler))

    liste = gecici / "liste.txt"
    liste.write_text("".join(f"file '{k.resolve()}'\n" for k in klipler), encoding="utf-8")
    gorsel_mp4 = gecici / "gorsel.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(liste),
                    "-c", "copy", str(gorsel_mp4)], check=True)

    ass = ass_dosyasi(zaman, bicim, boyut, marka, gecici / "yazilar.ass",
                      (zaman["sure"], toplam) if son_kart_sure > 0 else None)
    cikti = klasor / "video.mp4"
    vf = f"vignette=PI/5,ass={ass}:fontsdir={FONTLAR}"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(gorsel_mp4), "-i", str(ses),
        "-filter_complex", f"[0:v]{vf}[v];[1:a]apad=whole_dur={toplam:.3f}[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{toplam:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(cikti),
    ], check=True)

    srt_dosyasi(zaman, klasor / "altyazi.srt")
    (klasor / "kaynaklar.txt").write_text("\n".join(atiflar) + "\n", encoding="utf-8")
    rapor = {"video": str(cikti), "sure": toplam, "sahne_sayisi": len(sahneler), "uyarilar": uyarilar}
    (klasor / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    return rapor


def bolum_zamanlari(zaman: dict) -> list[tuple[str, str]]:
    """YouTube açıklaması için bölüm zaman damgaları (ilki 00:00)."""
    sonuc = []
    if zaman["paragraflar"] and not zaman["paragraflar"][0].get("bolum"):
        sonuc.append(("00:00", "Giriş"))
    for p in zaman["paragraflar"]:
        if p.get("bolum"):
            t = 0 if not sonuc else math.floor(p["baslangic"] - 0.9)
            m, s = divmod(max(0, t), 60)
            h, m = divmod(m, 60)
            sonuc.append((f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}", p["bolum"]))
    return sonuc
