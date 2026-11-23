"""Seslendirme kalite kontrolü (CLAUDE.md §3 madde 7).

Üretilen ses, faster-whisper ile yeniden yazıya çevrilir ve her paragraf, seslendirmeye
gönderilen metinle kelime kelime karşılaştırılır. Kelime hata oranı (WER) eşiği aşan
paragraflar rapora yazılır; böylece yanlış okunan kelimeler yüklemeden önce yakalanır.

Not: Edge TTS aynı metni her seferinde aynı okur; hatalı paragraf yeniden üretilerek
düzelmez. Düzeltme, senaryodaki yazımı veya `okunus` tablosunu değiştirerek yapılır.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

ESIK = 0.06      # paragraf başına izin verilen harf düzeyi hata oranı
BAS_SESSIZLIK = 1  # sn


def _norm(metin: str) -> list[str]:
    from derin.sayilar import cevir

    metin = cevir(metin)   # duyulan metindeki '1959' → 'bin dokuz yüz elli dokuz'
    metin = metin.replace("İ", "i").replace("I", "ı").lower()
    metin = metin.translate(str.maketrans("âîû", "aiu"))
    return [k for k in re.sub(r"[^\wçğıöşü\s]", " ", metin).split() if k]


def wer(beklenen: list[str], duyulan: list[str]) -> tuple[float, list[str]]:
    """Harf düzeyinde hata oranı (kelime birleşme/ayrılma farklarından etkilenmez) + kelime farkları."""
    a, b = "".join(beklenen), "".join(duyulan)
    oran = 1 - SequenceMatcher(a=a, b=b, autojunk=False).ratio()
    farklar = []
    for etiket, i1, i2, j1, j2 in SequenceMatcher(a=beklenen, b=duyulan, autojunk=False).get_opcodes():
        if etiket != "equal" and "".join(beklenen[i1:i2]) != "".join(duyulan[j1:j2]):
            farklar.append(f"'{' '.join(beklenen[i1:i2])}' → '{' '.join(duyulan[j1:j2])}'")
    return oran, farklar


def denetle(ses: Path, zaman: dict, konusmalar: list[str], model_boyutu: str = "small") -> dict:
    from faster_whisper import WhisperModel

    import subprocess

    import numpy as np

    # sesi kendimiz çözüyoruz (faster-whisper'ın PyAV sürüm uyumsuzluğundan bağımsız)
    ham = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ses), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    # Başa 1 sn sessizlik: Whisper, ses hemen başlayınca ilk kelimeleri atlayabiliyor (yanlış alarm).
    dalga = np.concatenate([np.zeros(16000 * BAS_SESSIZLIK, dtype=np.float32), np.frombuffer(ham, dtype=np.float32)])
    model = WhisperModel(model_boyutu, device="cpu", compute_type="int8")
    parcalar, _ = model.transcribe(dalga, language="tr", word_timestamps=True, vad_filter=False)
    kelimeler = [(w.word, w.start - BAS_SESSIZLIK, w.end - BAS_SESSIZLIK) for p in parcalar for w in (p.words or [])]

    sorunlu = []
    for p, konusma in zip(zaman["paragraflar"], konusmalar):
        duyulan = " ".join(k for k, b, e in kelimeler if b >= p["baslangic"] - 0.3 and e <= p["bitis"] + 0.3)
        oran, farklar = wer(_norm(konusma), _norm(duyulan))
        if oran > ESIK:
            sorunlu.append({"paragraf": p["sira"], "wer": round(oran, 3), "farklar": farklar[:12],
                            "metin": p["metin"][:120]})
    return {"esik": ESIK, "paragraf_sayisi": len(konusmalar), "sorunlu": sorunlu}
