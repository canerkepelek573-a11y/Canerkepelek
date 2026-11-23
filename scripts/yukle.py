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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bolum", type=Path)
    ap.add_argument("--gizlilik", default="private")
    ap.add_argument("--zamanla", action="store_true")
    arg = ap.parse_args()

    kok = Path("cikti") / arg.bolum.name
    bilgi = json.loads((kok / "yukleme.json").read_text(encoding="utf-8"))
    zamanlar = yayin_zamanlari(1 + len(bilgi["shorts"])) if arg.zamanla else [None] * (1 + len(bilgi["shorts"]))
    sonuc = {"yuklenen": []}

    a = bilgi["ana"]
    vid = youtube.yukle(kok / a["video"], a["baslik"], a["aciklama"], a["etiketler"], arg.gizlilik, zamanlar[0],
                        kapak=kok / a["kapak"], altyazi=kok / a["altyazi"])
    sonuc["yuklenen"].append({"tur": "ana", "id": vid, "yayin": zamanlar[0]})
    print(f"Ana video yüklendi: https://youtu.be/{vid}")
    for k, zaman in zip(bilgi["shorts"], zamanlar[1:]):
        sid = youtube.yukle(kok / k["video"], k["baslik"], k["aciklama"], k["etiketler"], arg.gizlilik, zaman)
        sonuc["yuklenen"].append({"tur": "shorts", "id": sid, "yayin": zaman})
        print(f"Shorts yüklendi: https://youtu.be/{sid}")

    if not all(youtube.dogrula(y["id"]) for y in sonuc["yuklenen"]):
        print("HATA: yükleme doğrulanamadı; dosyalar silinmedi.")
        return 1
    (arg.bolum / "yuklendi.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(kok, ignore_errors=True)        # §7: yükleme doğrulandıktan sonra üretim dosyalarını sil
    print("Yükleme doğrulandı, üretim dosyaları silindi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
