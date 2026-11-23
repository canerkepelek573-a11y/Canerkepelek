"""Edge TTS ses testi.

Aynı gizemli test paragrafını farklı ses ve ayarlarla seslendirir; kanal sahibi
dinleyip en beğendiği sesi seçer. Her ses için kelime zamanlamalı altyazı (.srt)
da üretilir (ses-görüntü-altyazı eşlemesinin çalıştığını göstermek için).

Kullanım: python scripts/ses_testi.py
Çıktılar: ornekler/ klasörüne .mp3, .srt ve sesler.txt
"""

import asyncio
import sys
from pathlib import Path

import edge_tts

KOK = Path(__file__).resolve().parent.parent
ORNEKLER = KOK / "ornekler"

METIN = (ORNEKLER / "test_metni.txt").read_text(encoding="utf-8").strip()
RAKAMLI = (ORNEKLER / "test_metni_rakamli.txt").read_text(encoding="utf-8").strip()

# (dosya adı, ses, hız, ses perdesi, metin)
DENEMELER = [
    ("01_ahmet_dogal", "tr-TR-AhmetNeural", "+0%", "+0Hz", METIN),
    ("02_ahmet_gizemli", "tr-TR-AhmetNeural", "-10%", "-5Hz", METIN),
    ("03_ahmet_cok_gizemli", "tr-TR-AhmetNeural", "-15%", "-10Hz", METIN),
    ("04_emel_gizemli", "tr-TR-EmelNeural", "-10%", "-3Hz", METIN),
    ("05_andrew_cok_dilli", "en-US-AndrewMultilingualNeural", "-8%", "-3Hz", METIN),
    ("06_florian_cok_dilli", "de-DE-FlorianMultilingualNeural", "-8%", "-3Hz", METIN),
    ("07_ahmet_rakamli_metin", "tr-TR-AhmetNeural", "-10%", "-5Hz", RAKAMLI),
]


async def ses_listesi() -> set[str]:
    sesler = await edge_tts.list_voices()
    secilen = [
        s for s in sesler
        if s["Locale"].startswith("tr-") or "Multilingual" in s["ShortName"]
    ]
    satirlar = [f'{s["ShortName"]}  ({s["Gender"]})' for s in sorted(secilen, key=lambda s: s["ShortName"])]
    (ORNEKLER / "sesler.txt").write_text(
        "Türkçe ve çok dilli Edge TTS sesleri\n\n" + "\n".join(satirlar) + "\n",
        encoding="utf-8",
    )
    return {s["ShortName"] for s in sesler}


async def seslendir(ad: str, ses: str, hiz: str, perde: str, metin: str) -> None:
    iletisim = edge_tts.Communicate(metin, ses, rate=hiz, pitch=perde, boundary="WordBoundary")
    altyazi = edge_tts.SubMaker()
    with open(ORNEKLER / f"{ad}.mp3", "wb") as f:
        async for parca in iletisim.stream():
            if parca["type"] == "audio":
                f.write(parca["data"])
            elif parca["type"] == "WordBoundary":
                altyazi.feed(parca)
    (ORNEKLER / f"{ad}.srt").write_text(altyazi.get_srt(), encoding="utf-8")


async def main() -> int:
    mevcut = await ses_listesi()
    hatalar = 0
    for ad, ses, hiz, perde, metin in DENEMELER:
        if ses not in mevcut:
            print(f"ATLANDI: {ad} — {ses} bu listede yok")
            continue
        try:
            await seslendir(ad, ses, hiz, perde, metin)
            print(f"TAMAM: {ad}")
        except Exception as hata:  # her denemeyi ayrı ayrı raporla
            hatalar += 1
            print(f"HATA: {ad} — {hata}")
    return 1 if hatalar == len(DENEMELER) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
