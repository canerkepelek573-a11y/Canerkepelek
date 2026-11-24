"""Üretilmiş bir bölümü YouTube'a yükler ve başarıdan sonra üretim dosyalarını siler (CLAUDE.md §5, §7).

Kullanım: python scripts/yukle.py bolumler/001-dyatlov [--gizlilik private|unlisted|public] [--zamanla]
--zamanla: ana video ve 1. Shorts bir sonraki 19:00 (TSİ) için; diğer Shorts'lar sonraki günlerde
           her gün birer tane 19:00'a planlanır (kanal sahibiyle kararlaştırılan düzen).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from derin import youtube  # noqa: E402

TSI = dt.timezone(dt.timedelta(hours=3))


def yayin_zamanlari(adet: int) -> list[str]:
    """[ana, shorts1, shorts2, ...]: ana + shorts1 aynı gün 19:00; sonraki Shorts'lar her gün bir tane."""
    simdi = dt.datetime.now(TSI)
    ilk = simdi.replace(hour=19, minute=0, second=0, microsecond=0)
    if ilk <= simdi + dt.timedelta(hours=2):
        ilk += dt.timedelta(days=1)
    gunler = [0, 0] + list(range(1, max(0, adet - 2) + 1))
    return [(ilk + dt.timedelta(days=g)).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            for g in gunler[:adet]]


def kalite_kapisi(kok: Path) -> list[str]:
    """Yüklemeden önce son kontrol: eksik görsel, hatalı ses, uzun Shorts varsa yükleme yapılmaz (CLAUDE.md §1, §3)."""
    sorunlar = []
    ozet_yol = kok / "ozet.json"
    if not ozet_yol.exists():
        return ["ozet.json yok"]
    ozet = json.loads(ozet_yol.read_text(encoding="utf-8"))
    sorunlar += [u for u in ozet.get("uyarilar", []) if "alınamadı" in u or "süre" in u]
    if ozet.get("ana", {}).get("sure_dk", 0) < 20:
        sorunlar.append(f"ana video 20 dakikadan kısa: {ozet.get('ana')}")
    # Ses denetimi ayrı bir işte de çalışabilir (ana video); sonucu hiç gelmediyse yükleme yapılmaz.
    for parca in ["ana"] + sorted(p.name for p in kok.glob("shorts*") if p.is_dir()):
        if (kok / parca / "video.mp4").exists() and not (kok / "onizleme" / f"{parca}_ses_kontrol.json").exists():
            sorunlar.append(f"{parca}: ses kontrolü sonucu yok")
    for f in sorted((kok / "onizleme").glob("*_ses_kontrol.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("hata") or d.get("sorunlu"):
            sorunlar.append(f"{f.name}: {d.get('hata') or d.get('sorunlu')}")
    return sorunlar


def oynatma_listesi(bolum: Path) -> str | None:
    """Senaryodaki `oynatma_listesi` alanı (§5.8: video konusuna uygun tema listesine eklenir)."""
    import yaml

    veri = yaml.safe_load((bolum / "senaryo.yaml").read_text(encoding="utf-8")) or {}
    return veri.get("oynatma_listesi")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bolum", type=Path)
    ap.add_argument("--gizlilik", default="private")
    ap.add_argument("--zamanla", action="store_true")
    arg = ap.parse_args()

    kok = Path("cikti") / arg.bolum.name
    sorunlar = kalite_kapisi(kok)
    if sorunlar:
        print("YÜKLENMEDİ — kalite kontrolünden geçmedi:")
        for s_ in sorunlar:
            print(" -", str(s_)[:300])
        return 1
    bilgi = json.loads((kok / "yukleme.json").read_text(encoding="utf-8"))
    zamanlar = yayin_zamanlari(1 + len(bilgi["shorts"])) if arg.zamanla else [None] * (1 + len(bilgi["shorts"]))
    sonuc = {"yuklenen": [], "uyarilar": [], "dogrulandi": False}
    kayit = arg.bolum / "yuklendi.json"

    def kaydet() -> None:        # her yüklemeden sonra: yarıda kalsa bile hangi videoların yüklendiği bilinsin
        kayit.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")

    a = bilgi["ana"]
    vid = youtube.yukle(kok / a["video"], a["baslik"], a["aciklama"], a["etiketler"], arg.gizlilik, zamanlar[0],
                        kapak=kok / a["kapak"], altyazi=kok / a["altyazi"], uyarilar=sonuc["uyarilar"])
    sonuc["yuklenen"].append({"tur": "ana", "id": vid, "yayin": zamanlar[0]})
    kaydet()
    print(f"Ana video yüklendi: https://youtu.be/{vid}", flush=True)
    liste = oynatma_listesi(arg.bolum)
    if liste:
        sonuc["oynatma_listesi"] = liste
        youtube.listeye_ekle(vid, liste, sonuc["uyarilar"])
    for k, zaman in zip(bilgi["shorts"], zamanlar[1:]):
        sid = youtube.yukle(kok / k["video"], k["baslik"], k["aciklama"], k["etiketler"], arg.gizlilik, zaman,
                            uyarilar=sonuc["uyarilar"])
        sonuc["yuklenen"].append({"tur": "shorts", "id": sid, "yayin": zaman})
        kaydet()
        print(f"Shorts yüklendi: https://youtu.be/{sid}", flush=True)

    if not all(youtube.dogrula(y["id"], arg.gizlilik, y["yayin"]) for y in sonuc["yuklenen"]):
        kaydet()
        print("HATA: yükleme istenen durumda değil (gizliye kilitlenmiş veya zamanlama kaybolmuş olabilir); "
              "dosyalar silinmedi.")
        return 1
    sonuc["dogrulandi"] = True
    for u in sonuc["uyarilar"]:
        print("UYARI:", u)
    kaydet()
    shutil.rmtree(kok, ignore_errors=True)        # §7: yükleme doğrulandıktan sonra üretim dosyalarını sil
    print("Yükleme doğrulandı, üretim dosyaları silindi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
