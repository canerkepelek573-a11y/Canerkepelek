"""Senaryo dosyasını (YAML) okur ve seslendirmeye hazır paragraflara çevirir.

Senaryo biçimi (bolumler/<klasor>/senaryo.yaml):

    bolum_no: 1
    baslik: "..."
    okunus:                 # yabancı isimlerin Türkçe okunuşu (yazılış: okunuş)
      Dyatlov: Dyatlof
    akis:                   # ana video
      - bolum: "Giriş: ..."          # (isteğe bağlı) YouTube bölümü başlar
        yazi: "1 Şubat 1959"         # (isteğe bağlı) ekranda alt bilgi yazısı
        gorseller: [...]             # bu paragrafta sırayla gösterilecek görseller
        metin: >                     # anlatıcının okuyacağı paragraf
          ...
        sessizlik: 1.5               # (isteğe bağlı) paragraftan sonra ek sessizlik (sn)
      - abone: true                  # bir sonraki paragrafta "Abone Ol" yazısı çıkar
    shorts:
      - baslik: "..."
        akis: [...]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from derin.sayilar import cevir, kontrol


@dataclass
class Paragraf:
    sira: int
    metin: str                      # ekranda/altyazıda görünen yazılış
    konusma: str                    # seslendirmeye giden okunuş
    gorseller: list[dict] = field(default_factory=list)
    bolum: str | None = None
    yazi: str | None = None
    abone: bool = False
    sessizlik: float = 0.0


CUMLE_SINIRI = re.compile(r'(?<=[.!?…])\s+(?=[A-ZÇĞİÖŞÜ"“])')   # ses.py ile aynı cümle sınırı


def okunus_uygula(metin: str, okunus: dict[str, str]) -> str:
    """Yabancı isimleri Türkçe okunuşlarıyla değiştirir (uzun isimler önce)."""
    for yazilis in sorted(okunus, key=len, reverse=True):
        metin = re.sub(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){re.escape(yazilis)}", okunus[yazilis], metin)
    return metin


def _temizle(metin: str) -> str:
    return re.sub(r"\s+", " ", metin).strip()


def paragraflar(akis: list[dict], okunus: dict[str, str]) -> list[Paragraf]:
    sonuc: list[Paragraf] = []
    abone_bekliyor = False
    for oge in akis:
        if oge.get("abone") and "metin" not in oge:
            abone_bekliyor = True
            continue
        metin = _temizle(oge["metin"])
        konusma = cevir(okunus_uygula(metin, okunus))
        kontrol(konusma)
        sonuc.append(
            Paragraf(
                sira=len(sonuc),
                metin=metin,
                konusma=konusma,
                gorseller=oge.get("gorseller", []),
                bolum=oge.get("bolum"),
                yazi=oge.get("yazi"),
                abone=abone_bekliyor or bool(oge.get("abone")),
                sessizlik=float(oge.get("sessizlik", 0)),
            )
        )
        abone_bekliyor = False
    return sonuc


def oku(yol: Path) -> dict:
    with open(yol, encoding="utf-8") as f:
        veri = yaml.safe_load(f)
    okunus = veri.get("okunus", {}) or {}
    veri["paragraflar"] = paragraflar(veri["akis"], okunus)
    for kisa in veri.get("shorts", []) or []:
        if "paragraflar" in kisa:
            # Shorts = ana videonun seçilen anları (aynı anlatım, aynı görseller; CLAUDE.md §1)
            # Öğe: paragraf numarası (ör. 29) ya da {p: 29, cumleler: [0, 1]} — o paragrafın seçilen cümleleri
            secilen = []
            for yeni_sira, oge in enumerate(kisa["paragraflar"]):
                i = oge["p"] if isinstance(oge, dict) else oge
                ana = veri["paragraflar"][i]
                metin = ana.metin
                if isinstance(oge, dict) and "cumleler" in oge:
                    cumleler = CUMLE_SINIRI.split(ana.metin)
                    metin = " ".join(cumleler[j] for j in oge["cumleler"])
                konusma = cevir(okunus_uygula(metin, okunus))
                kontrol(konusma)
                secilen.append(Paragraf(sira=yeni_sira, metin=metin, konusma=konusma,
                                        gorseller=ana.gorseller, bolum=None, yazi=ana.yazi, abone=False,
                                        sessizlik=0.0))
            kisa["paragraflar"] = secilen
        else:
            kisa["paragraflar"] = paragraflar(kisa["akis"], okunus)
    return veri
