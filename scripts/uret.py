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


def yukleme_bilgisi(veri: dict, kok: Path) -> None:
    """Yükleme için tüm metadatayı (başlık, açıklama, etiket, hashtag) tek yerde toplar (CLAUDE.md §5)."""
    hashtag = " ".join(veri.get("hashtagler", []))
    ana_aciklama = (kok / "ana" / "aciklama.txt").read_text(encoding="utf-8") if (kok / "ana" / "aciklama.txt").exists() else ""
    bilgi = {"ana": {"baslik": veri["baslik"], "aciklama": ana_aciklama, "etiketler": veri.get("etiketler", []),
                     "video": "ana/video.mp4", "altyazi": "ana/altyazi.srt", "kapak": "kapak.jpg"},
             "shorts": []}
    for i, kisa in enumerate(veri.get("shorts", []) or [], 1):
        aciklama_k = f"{kisa.get('aciklama', '')}\n\nTam belgesel: {veri['baslik']}\n\n{hashtag} #Shorts"
        bilgi["shorts"].append({"baslik": kisa["baslik"], "aciklama": aciklama_k, "etiketler": veri.get("etiketler", []),
                                "video": f"shorts{i}/video.mp4"})
    (kok / "yukleme.json").write_text(json.dumps(bilgi, ensure_ascii=False, indent=1), encoding="utf-8")
    satirlar = [f"# Yükleme bilgileri — {veri['baslik']}", "", "## Ana video", f"**Başlık:** {veri['baslik']}", "",
                "**Etiketler:** " + ", ".join(veri.get("etiketler", [])), "", "**Açıklama:**", "", "```", ana_aciklama, "```", ""]
    for i, k in enumerate(bilgi["shorts"], 1):
        satirlar += [f"## Shorts {i}", f"**Başlık:** {k['baslik']}", "", "```", k["aciklama"], "```", ""]
    (kok / "onizleme").mkdir(parents=True, exist_ok=True)
    (kok / "onizleme" / "yukleme_bilgileri.md").write_text("\n".join(satirlar), encoding="utf-8")


async def sesi_uret(paragraflar, klasor: Path) -> dict:
    return await seslendir(paragraflar, klasor)


KONTROL = False


def uret_bir(ad: str, paragraflar, bicim: str, kok: Path, **kwargs) -> tuple[dict, dict]:
    klasor = kok / ad
    zaman = asyncio.run(sesi_uret(paragraflar, klasor))
    if KONTROL:
        from derin import kontrol
        try:
            sonuc = kontrol.denetle(klasor / "ses.wav", zaman, [p.konusma for p in paragraflar])
        except Exception as hata:      # kontrol aracı bozulursa video yine üretilsin, durum raporlansın
            sonuc = {"hata": f"Ses kontrolü çalışmadı: {type(hata).__name__}: {hata}"}
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
    ap.add_argument("--sadece", default="hepsi", help="ana | shorts1..shorts4 | kapak | bilgi | hepsi")
    ap.add_argument("--kontrol", action="store_true", help="sesi yazıya çevirip metinle karşılaştır")
    ap.add_argument("--yeniden-kontrol", default="",
                    help="üretilmiş parçaların sesini yeniden denetle (ör. ana,shorts1); render yapılmaz")
    arg = ap.parse_args()
    global KONTROL
    KONTROL = arg.kontrol

    veri = senaryo.oku(arg.bolum / "senaryo.yaml")
    kok = Path("cikti") / arg.bolum.name
    kok.mkdir(parents=True, exist_ok=True)
    ozet: dict = {"bolum": arg.bolum.name, "baslik": veri["baslik"], "uyarilar": []}

    if arg.yeniden_kontrol:
        from derin import kontrol
        listeler = {"ana": veri["paragraflar"]}
        listeler.update({f"shorts{i}": k["paragraflar"] for i, k in enumerate(veri.get("shorts", []) or [], 1)})
        for parca in arg.yeniden_kontrol.split(","):
            zaman = json.loads((kok / parca / "zaman.json").read_text(encoding="utf-8"))
            sonuc = kontrol.denetle(kok / parca / "ses.wav", zaman, [p.konusma for p in listeler[parca]])
            (kok / "onizleme").mkdir(parents=True, exist_ok=True)
            (kok / "onizleme" / f"{parca}_ses_kontrol.json").write_text(
                json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
            print(parca, json.dumps(sonuc, ensure_ascii=False, indent=1))
        return 0

    if arg.sadece == "gorseller":
        # Tüm arşiv görsellerini render'dan önce tek seferde, sırayla indirir (önbelleğe).
        # Paralel işler aynı anda Wikimedia'ya yüklenip "çok fazla istek" hatası almasın diye.
        from derin import gorsel
        tanimlar = [g for p in veri["paragraflar"] for g in p.gorseller]
        tanimlar += [g for k in veri.get("shorts", []) or [] for p in k["paragraflar"] for g in p.gorseller]
        tanimlar.append(veri["kapak"]["gorsel"])
        gorulen, hatalar = set(), []
        for t in tanimlar:
            anahtar = json.dumps(t, sort_keys=True, ensure_ascii=False)
            if t.get("kaynak") in ("kart", "harita") or anahtar in gorulen:
                continue
            gorulen.add(anahtar)
            try:
                gorsel.coz(t, kok / "gecici_gorsel", (1920, 1080))
            except Exception as hata:
                hatalar.append(f"{t}: {type(hata).__name__}: {hata}")
        print(f"{len(gorulen)} görsel denendi, {len(hatalar)} hata")
        for h in hatalar:
            print("HATA:", h)
        return 1 if hatalar else 0

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
        zaman, rapor = uret_bir(f"shorts{i}", kisa["paragraflar"], "shorts", kok, son_kart_sure=2.5,
                                son_kart={"kaynak": "kart", "ust": "Gerçek Gizem", "baslik": "Tam Belgesel Kanalda",
                                          "alt": veri["baslik"].split(":")[0]})
        ozet[f"shorts{i}"] = {"sure_sn": round(rapor["sure"], 1), "sahne": rapor["sahne_sayisi"]}
        ozet["uyarilar"] += [f"shorts{i}: {u}" for u in rapor["uyarilar"]]
        if rapor["sure"] > 60:
            ozet["uyarilar"].append(f"shorts{i}: süre {rapor['sure']:.0f} sn (hedef 20–50 sn)")

    if arg.sadece in ("hepsi", "bilgi"):
        yukleme_bilgisi(veri, kok)

    if arg.sadece == "hepsi" and (kok / "kapak.jpg").exists():
        (kok / "onizleme").mkdir(exist_ok=True)
        shutil.copy(kok / "kapak.jpg", kok / "onizleme" / "kapak.jpg")
    ad = "ozet.json" if arg.sadece == "hepsi" else f"ozet_{arg.sadece}.json"
    (kok / ad).write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
