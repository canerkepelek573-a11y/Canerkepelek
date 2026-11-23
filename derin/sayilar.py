"""Türkçe metindeki sayıları, sembolleri ve kısaltmaları konuşma diline çevirir.

Seslendirme hiçbir zaman rakam görmez: rakamlar kesik okunabilir ve Edge TTS
rakamlar için kelime zamanlaması vermez (altyazı/görüntü eşlemesi bozulur).
Bu yüzden metin seslendirmeden önce tamamen yazıya çevrilir ve `kontrol()`
ile rakam, sembol ya da kısaltma kalmadığı doğrulanır.

Örnekler:
    1947'de        -> bin dokuz yüz kırk yedide
    1990'larda     -> bin dokuz yüz doksanlarda
    10.000         -> on bin
    3,5 km         -> üç buçuk kilometre
    3,05           -> üç virgül sıfır beş
    %40'ı          -> yüzde kırkı
    -30 derece     -> eksi otuz derece
    21. yüzyıl     -> yirmi birinci yüzyıl
    II. Dünya      -> İkinci Dünya
    M.Ö. 300       -> milattan önce üç yüz
    23:30          -> yirmi üç otuz
"""

from __future__ import annotations

import re

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
BUYUK = [(10**12, "trilyon"), (10**9, "milyar"), (10**6, "milyon"), (1000, "bin")]

UNLULER = "aeıioöuü"
SIRA_EKI = {"a": "ıncı", "ı": "ıncı", "e": "inci", "i": "inci", "o": "uncu", "u": "uncu", "ö": "üncü", "ü": "üncü"}


def _uc_basamak(n: int) -> list[str]:
    yuz, kalan = divmod(n, 100)
    on, bir = divmod(kalan, 10)
    kelimeler = []
    if yuz:
        if yuz > 1:
            kelimeler.append(BIRLER[yuz])
        kelimeler.append("yüz")
    if on:
        kelimeler.append(ONLAR[on])
    if bir:
        kelimeler.append(BIRLER[bir])
    return kelimeler


def sayi_yazi(n: int) -> str:
    """Tam sayıyı Türkçe yazıya çevirir: 1947 -> 'bin dokuz yüz kırk yedi'."""
    if n == 0:
        return "sıfır"
    if n < 0:
        return "eksi " + sayi_yazi(-n)
    kelimeler: list[str] = []
    for deger, ad in BUYUK:
        grup, n = divmod(n, deger)
        if grup:
            if not (ad == "bin" and grup == 1):
                kelimeler.extend(sayi_yazi(grup).split())
            kelimeler.append(ad)
    kelimeler.extend(_uc_basamak(n))
    return " ".join(kelimeler)


def _son_unlu(kelime: str) -> str:
    for harf in reversed(kelime):
        if harf in UNLULER:
            return harf
    return "e"


def sira_yazi(n: int) -> str:
    """Sıra sayısı: 21 -> 'yirmi birinci', 4 -> 'dördüncü'."""
    kelimeler = sayi_yazi(n).split()
    son = kelimeler[-1]
    if son == "dört":
        son = "dörd"
    ek = SIRA_EKI[_son_unlu(son)]
    if son[-1] in UNLULER:
        ek = ek[1:]
    kelimeler[-1] = son + ek
    return " ".join(kelimeler)


def _ek_ekle(okunus: str, ek: str) -> str:
    """Kesme işaretli eki okunuşa ekler; 'dört' + ünlüyle başlayan ek -> 'dörd'."""
    if not ek:
        return okunus
    if okunus.endswith("dört") and ek[0] in UNLULER:
        okunus = okunus[:-1] + "d"
    return okunus + ek


def ondalik_yazi(tam: str, kesir: str) -> str:
    """3,5 -> 'üç buçuk'; 3,05 -> 'üç virgül sıfır beş'; 12,25 -> 'on iki virgül yirmi beş'."""
    tam_okunus = sayi_yazi(int(tam))
    if kesir == "5":
        return f"{tam_okunus} buçuk"
    sifirlar = len(kesir) - len(kesir.lstrip("0"))
    kalan = kesir.lstrip("0")
    parcalar = ["sıfır"] * sifirlar
    if kalan:
        parcalar.append(sayi_yazi(int(kalan)))
    return f"{tam_okunus} virgül {' '.join(parcalar)}"


ROMA = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roma_deger(s: str) -> int | None:
    if not s or any(h not in ROMA for h in s):
        return None
    toplam = 0
    for i, h in enumerate(s):
        d = ROMA[h]
        if i + 1 < len(s) and ROMA[s[i + 1]] > d:
            toplam -= d
        else:
            toplam += d
    # yalnızca kurallı (yeniden yazıldığında aynı çıkan) Roma rakamlarını kabul et
    return toplam if _roma_yaz(toplam) == s else None


def _roma_yaz(n: int) -> str:
    tablo = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
             (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for d, h in tablo:
        while n >= d:
            s += h
            n -= d
    return s


def _buyuk_harfle(metin: str) -> str:
    kelimeler = metin.split()
    return " ".join(("İ" + k[1:]) if k[0] == "i" else k[0].upper() + k[1:] for k in kelimeler)


KISALTMALAR = [
    (r"\bM\.\s?Ö\.", "milattan önce"),
    (r"\bM\.\s?S\.", "milattan sonra"),
    (r"\bvb\.", "ve benzeri"),
    (r"\bvs\.", "vesaire"),
    (r"\bDr\.", "Doktor"),
    (r"\bProf\.", "Profesör"),
    (r"\bdk\.", "dakika"),
    (r"\bsn\.", "saniye"),
]

BIRIMLER = {
    "km": "kilometre", "m": "metre", "cm": "santimetre", "mm": "milimetre",
    "kg": "kilogram", "g": "gram", "°C": "derece", "°": "derece", "sa": "saat",
}

EK = r"(?:['’]([a-zçğıöşüA-ZÇĞİÖŞÜ]+))?"
SAYI = r"\d{1,3}(?:\.\d{3})+|\d+"


def _tam(s: str) -> int:
    return int(s.replace(".", ""))


def cevir(metin: str) -> str:
    """Metindeki tüm sayı, sembol ve kısaltmaları konuşma diline çevirir."""
    for desen, yerine in KISALTMALAR:
        metin = re.sub(desen, yerine, metin)

    # Roma rakamı + nokta + büyük harfle başlayan kelime: "II. Dünya" -> "İkinci Dünya"
    def roma(m: re.Match) -> str:
        deger = roma_deger(m.group(1))
        return m.group(0) if deger is None else _buyuk_harfle(sira_yazi(deger)) + " "

    metin = re.sub(r"\b([IVXLCDM]+)\.\s+(?=[A-ZÇĞİÖŞÜ])", roma, metin)

    # Saat: 23:30
    metin = re.sub(
        r"\b(\d{1,2}):(\d{2})\b",
        lambda m: sayi_yazi(int(m.group(1))) + (" " + sayi_yazi(int(m.group(2))) if int(m.group(2)) else ""),
        metin,
    )

    # Yüzde: %40, % 3,5, %40'ı
    def yuzde(m: re.Match) -> str:
        okunus = ondalik_yazi(m.group(1).replace(".", ""), m.group(2)) if m.group(2) else sayi_yazi(_tam(m.group(1)))
        return "yüzde " + _ek_ekle(okunus, m.group(3) or "")

    metin = re.sub(rf"%\s?({SAYI})(?:,(\d+))?{EK}", yuzde, metin)

    # Sayı aralığı: 1959-1960 -> "... ile ..."
    metin = re.sub(rf"(?<=\d)\s?[–-]\s?(?=\d)", " ile ", metin)

    # Sıra sayısı: "21. yüzyıl" (noktadan sonra küçük harfle devam eden kelime)
    metin = re.sub(
        rf"(?<![\d,.])({SAYI})\.(?=\s+[a-zçğıöşü])",
        lambda m: sira_yazi(_tam(m.group(1))),
        metin,
    )

    # Negatif sayı: boşluk/başlangıçtan sonra gelen "-30"
    metin = re.sub(r"(^|(?<=[\s(]))-(?=\d)", "eksi ", metin)

    # Ondalık ve tam sayılar (+ kesme işaretli ek, + birim)
    birim_deseni = "|".join(re.escape(b) for b in sorted(BIRIMLER, key=len, reverse=True))

    def sayi(m: re.Match) -> str:
        okunus = ondalik_yazi(m.group(1).replace(".", ""), m.group(2)) if m.group(2) else sayi_yazi(_tam(m.group(1)))
        okunus = _ek_ekle(okunus, m.group(3) or "")
        if m.group(4):
            okunus += " " + BIRIMLER[m.group(4)]
        return okunus

    metin = re.sub(
        rf"(?<![\w.,])({SAYI})(?:,(\d+))?{EK}(?:\s?({birim_deseni})(?![\wçğıöşü]))?",
        sayi,
        metin,
    )

    metin = metin.replace("&", " ve ")
    return re.sub(r"[ \t]{2,}", " ", metin)


YASAK = re.compile(r"[\d%&/°]|\b(?:vb|vs|Dr|Prof)\.")


class SeslendirmeMetniHatasi(ValueError):
    pass


def kontrol(metin: str) -> None:
    """Seslendirmeye gidecek metinde rakam, sembol veya kısaltma kalmışsa durdurur."""
    hatalar = [m.group(0) for m in YASAK.finditer(metin)]
    if hatalar:
        raise SeslendirmeMetniHatasi(f"Seslendirme metninde çevrilmemiş öğe var: {sorted(set(hatalar))}")
