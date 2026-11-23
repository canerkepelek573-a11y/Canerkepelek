"""Edge TTS ile paragraf paragraf seslendirme ve kelime/cümle zaman çizelgesi.

Her paragraf ayrı seslendirilir; Edge'in verdiği kelime zamanlamaları (WordBoundary)
saklanır. Paragraflar, sonlarındaki fazla sessizlik kırpılarak ve araya kontrollü
sessizlik konarak tek bir WAV dosyasında birleştirilir. Ortaya çıkan zaman çizelgesi
(zaman.json) görüntü geçişleri ve altyazılar için tek doğruluk kaynağıdır.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import subprocess
import wave
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import edge_tts

from derin.senaryo import Paragraf

SES = "tr-TR-AhmetNeural"
HIZ = "-10%"
PERDE = "-5Hz"

ORNEKLEME = 24000
PARAGRAF_ARASI = 0.55      # sn
BOLUM_ONCESI = 1.2         # yeni YouTube bölümü başlamadan önce ek sessizlik
SON_PAY = 0.20             # son kelimeden sonra bırakılan doğal kuyruk
BASTAKI_SESSIZLIK = 0.4    # videonun en başında

ONBELLEK = Path(".onbellek/ses")
DENEME = 4


@dataclass
class Kelime:
    yazi: str
    baslangic: float
    bitis: float


async def _edge(konusma: str, mp3: Path) -> list[Kelime]:
    iletisim = edge_tts.Communicate(konusma, SES, rate=HIZ, pitch=PERDE, boundary="WordBoundary")
    kelimeler: list[Kelime] = []
    with open(mp3, "wb") as f:
        async for parca in iletisim.stream():
            if parca["type"] == "audio":
                f.write(parca["data"])
            elif parca["type"] == "WordBoundary":
                bas = parca["offset"] / 1e7
                kelimeler.append(Kelime(parca["text"], bas, bas + parca["duration"] / 1e7))
    return kelimeler


async def paragraf_sesi(konusma: str) -> tuple[Path, list[Kelime]]:
    """Paragrafı seslendirir (önbellekli). Hata olursa birkaç kez tekrar dener."""
    ONBELLEK.mkdir(parents=True, exist_ok=True)
    anahtar = hashlib.sha1(f"{SES}|{HIZ}|{PERDE}|{konusma}".encode()).hexdigest()[:16]
    mp3, js = ONBELLEK / f"{anahtar}.mp3", ONBELLEK / f"{anahtar}.json"
    if mp3.exists() and js.exists():
        return mp3, [Kelime(**k) for k in json.loads(js.read_text(encoding="utf-8"))]

    son_hata: Exception | None = None
    for deneme in range(DENEME):
        try:
            kelimeler = await _edge(konusma, mp3)
            if not kelimeler or mp3.stat().st_size < 1000:
                raise RuntimeError("Edge TTS boş ses döndürdü")
            js.write_text(json.dumps([k.__dict__ for k in kelimeler], ensure_ascii=False), encoding="utf-8")
            return mp3, kelimeler
        except Exception as hata:  # ağ hataları vb.
            son_hata = hata
            await asyncio.sleep(2 * (deneme + 1))
    raise RuntimeError(f"Seslendirme başarısız: {son_hata}") from son_hata


def _pcm(mp3: Path) -> bytes:
    """MP3'ü 24 kHz mono 16-bit PCM'e çözer."""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(ORNEKLEME), "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout


def _sessizlik(sn: float) -> bytes:
    return b"\x00\x00" * int(round(sn * ORNEKLEME))


def _norm(s: str) -> str:
    return re.sub(r"[^\wçğıöşü]", "", s.lower().replace("İ", "i").replace("I", "ı"))


def cumle_zamanlari(konusma: str, kelimeler: list[Kelime]) -> list[dict]:
    """Paragraftaki her cümlenin başlangıç/bitiş zamanını kelime zamanlamalarından bulur."""
    cumleler = [c for c in re.split(r"(?<=[.!?…])\s+(?=[A-ZÇĞİÖŞÜ\"“])", konusma.strip()) if c]
    bizim: list[tuple[int, str]] = []       # (cümle no, normalize kelime)
    for i, c in enumerate(cumleler):
        for k in c.split():
            n = _norm(k)
            if n:
                bizim.append((i, n))
    onlarin = [_norm(k.yazi) for k in kelimeler]
    eslesme = SequenceMatcher(a=[b for _, b in bizim], b=onlarin, autojunk=False)

    karsilik: dict[int, int] = {}
    for blok in eslesme.get_matching_blocks():
        for j in range(blok.size):
            karsilik[blok.a + j] = blok.b + j

    sonuc = []
    for i, metin in enumerate(cumleler):
        idx = [karsilik[a] for a, (ci, _) in enumerate(bizim) if ci == i and a in karsilik]
        if idx:
            sonuc.append({"metin": metin, "baslangic": kelimeler[min(idx)].baslangic, "bitis": kelimeler[max(idx)].bitis})
        else:
            sonuc.append({"metin": metin, "baslangic": None, "bitis": None})
    # eşleşmeyen cümleleri komşularına göre doldur
    for i, c in enumerate(sonuc):
        if c["baslangic"] is None:
            onceki = sonuc[i - 1]["bitis"] if i else 0.0
            sonraki = next((s["baslangic"] for s in sonuc[i + 1:] if s["baslangic"] is not None), kelimeler[-1].bitis)
            c["baslangic"], c["bitis"] = onceki, sonraki
    return sonuc


async def seslendir(paragraflar: list[Paragraf], klasor: Path) -> dict:
    """Tüm paragrafları seslendirir; klasor/ses.wav ve klasor/zaman.json üretir."""
    klasor.mkdir(parents=True, exist_ok=True)
    parcalar: list[bytes] = [_sessizlik(BASTAKI_SESSIZLIK)]
    an = BASTAKI_SESSIZLIK
    cizelge = []

    for p in paragraflar:
        if p.bolum and p.sira > 0:
            parcalar.append(_sessizlik(BOLUM_ONCESI))
            an += BOLUM_ONCESI
        mp3, kelimeler = await paragraf_sesi(p.konusma)
        pcm = _pcm(mp3)
        kesim = min(len(pcm) // 2, int((kelimeler[-1].bitis + SON_PAY) * ORNEKLEME))
        pcm = pcm[: kesim * 2]
        sure = kesim / ORNEKLEME

        cizelge.append({
            "sira": p.sira,
            "bolum": p.bolum,
            "yazi": p.yazi,
            "abone": p.abone,
            "gorseller": p.gorseller,
            "metin": p.metin,
            "baslangic": round(an, 3),
            "bitis": round(an + sure, 3),
            "kelimeler": [[k.yazi, round(an + k.baslangic, 3), round(an + k.bitis, 3)] for k in kelimeler],
            "cumleler": [
                {**c, "baslangic": round(an + c["baslangic"], 3), "bitis": round(an + c["bitis"], 3)}
                for c in cumle_zamanlari(p.konusma, kelimeler)
            ],
        })
        parcalar.append(pcm)
        an += sure
        bosluk = PARAGRAF_ARASI + p.sessizlik
        parcalar.append(_sessizlik(bosluk))
        an += bosluk

    with wave.open(str(klasor / "ses.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(ORNEKLEME)
        w.writeframes(b"".join(parcalar))

    zaman = {"sure": round(an, 3), "paragraflar": cizelge}
    (klasor / "zaman.json").write_text(json.dumps(zaman, ensure_ascii=False, indent=1), encoding="utf-8")
    return zaman
