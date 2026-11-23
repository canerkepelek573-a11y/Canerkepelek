"""Bir bölümün tüm paketini üretir: ana video, Shorts'lar, kapak, açıklama.

Kullanım:
    python scripts/uret.py bolumler/001-dyatlov            # her şey
    python scripts/uret.py bolumler/001-dyatlov --sadece ana
    python scripts/uret.py bolumler/001-dyatlov --sadece shorts1

Çıktılar cikti/<bolum>/ altına yazılır (depoya eklenmez).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from derin import kapak, senaryo, video  # noqa: E402
from derin.ses import seslendir  # noqa: E402

ACIKLAMA_SINIRI = 4900


def aciklama(veri: dict, zaman: dict, atiflar: list[str]) -> str:
    parcalar = [veri["aciklama"].strip(), ""]
    bolumler = video.bolum_zamanlari(zaman)
    if len(bolumler) >= 3:
        parcalar += ["BÖLÜMLER"] + [f"{z} {ad}" for z, ad in bolumler] + [""]
    if veri.get("kaynaklar"):
        parcalar += ["KAYNAKLAR VE OKUMA ÖNERİLERİ"] + [f"• {k}" for k in veri["kaynaklar"]] + [""]
    parcalar += [
        "Bu videoda anlatılan söylenti ve iddialar, iddia olarak aktarılmıştır; karar sizin.",
        "Seslendirme yapay zekâ ile üretilmiştir. Videoda müzik ve ses efekti kullanılmamıştır.",
        "",
    ]
    gorsel_bolumu = ["GÖRSEL KAYNAKLARI VE LİSANSLARI"] + [f"• {a}" for a in atiflar] + [""]
    etiket_satiri = " ".join(veri.get("hashtagler", []))
    metin = "\n".join(parcalar + gorsel_bolumu + [etiket_satiri])
    if len(metin) > ACIKLAMA_SINIRI:   # atıflar çok uzunsa kısalt ama lisans türünü koru
        kisa = ["GÖRSEL KAYNAKLARI VE LİSANSLARI"] + [f"• {a[:160]}" for a in atiflar] + [""]
        metin = "\n".join(parcalar + kisa + [etiket_satiri])[:ACIKLAMA_SINIRI]
    return metin


async def sesi_uret(paragraflar, klasor: Path) -> dict:
    return await seslendir(paragraflar, klasor)


KONTROL = False


def uret_bir(ad: str, paragraflar, bicim: str, kok: Path, **kwargs) -> tuple[dict, dict]:
    klasor = kok / ad
    zaman = asyncio.run(sesi_uret(paragraflar, klasor))
    if KONTROL:
        from derin import kontrol
        sonuc = kontrol.denetle(klasor / "ses.wav", zaman, [p.konusma for p in paragraflar])
        (kok / "onizleme").mkdir(parents=True, exist_ok=True)
        (kok / "onizleme" / f"{ad}_ses_kontrol.json").write_text(
            json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor = video.olustur(zaman, klasor / "ses.wav", bicim, klasor, **kwargs)
    for t in (2, zaman["sure"] * 0.3, zaman["sure"] * 0.6):     # kontrol için örnek kareler
        hedef = kok / "onizleme" / f"{ad}_{int(t):05d}.jpg"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", rapor["video"],
                        "-frames:v", "1", "-vf", "scale=960:-2", str(hedef)], check=False)
    shutil.rmtree(klasor / "gecici", ignore_errors=True)
    return zaman, rapor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bolum", type=Path)
    ap.add_argument("--sadece", default="hepsi", help="ana | shorts1..shorts4 | kapak | hepsi")
    ap.add_argument("--kontrol", action="store_true", help="sesi yazıya çevirip metinle karşılaştır")
    arg = ap.parse_args()
    global KONTROL
    KONTROL = arg.kontrol

    veri = senaryo.oku(arg.bolum / "senaryo.yaml")
    kok = Path("cikti") / arg.bolum.name
    kok.mkdir(parents=True, exist_ok=True)
    ozet: dict = {"bolum": arg.bolum.name, "baslik": veri["baslik"], "uyarilar": []}

    if arg.sadece in ("hepsi", "kapak"):
        kapak.olustur(veri["kapak"], veri["bolum_no"], kok / "kapak.jpg")

    if arg.sadece in ("hepsi", "ana"):
        zaman, rapor = uret_bir("ana", veri["paragraflar"], "ana", kok, son_kart_sure=15.0,
                                son_kart=veri.get("son_kart"))
        atiflar = (kok / "ana" / "kaynaklar.txt").read_text(encoding="utf-8").split("\n")
        (kok / "ana" / "aciklama.txt").write_text(aciklama(veri, zaman, [a for a in atiflar if a]), encoding="utf-8")
        ozet["ana"] = {"sure_dk": round(rapor["sure"] / 60, 1), "sahne": rapor["sahne_sayisi"]}
        ozet["uyarilar"] += rapor["uyarilar"]

    for i, kisa in enumerate(veri.get("shorts", []) or [], 1):
        if arg.sadece not in ("hepsi", f"shorts{i}"):
            continue
        zaman, rapor = uret_bir(f"shorts{i}", kisa["paragraflar"], "shorts", kok)
        ozet[f"shorts{i}"] = {"sure_sn": round(rapor["sure"], 1), "sahne": rapor["sahne_sayisi"]}
        ozet["uyarilar"] += [f"shorts{i}: {u}" for u in rapor["uyarilar"]]
        if rapor["sure"] > 60:
            ozet["uyarilar"].append(f"shorts{i}: süre {rapor['sure']:.0f} sn (hedef 20–50 sn)")

    if arg.sadece == "hepsi" and (kok / "kapak.jpg").exists():
        (kok / "onizleme").mkdir(exist_ok=True)
        shutil.copy(kok / "kapak.jpg", kok / "onizleme" / "kapak.jpg")
    (kok / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
