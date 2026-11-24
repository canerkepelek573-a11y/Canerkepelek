"""Yüklenmiş ana videoyu oynatma listesine ekler (yükleme sırasında geçici hata olduysa sonradan tekrar).

Kullanım: python scripts/listeye_ekle.py bolumler/001-dyatlov
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from derin import youtube  # noqa: E402
from yukle import oynatma_listesi  # noqa: E402


def main() -> int:
    bolum = Path(sys.argv[1])
    kayit = bolum / "yuklendi.json"
    sonuc = json.loads(kayit.read_text(encoding="utf-8"))
    liste = oynatma_listesi(bolum)
    if not liste:
        print("Senaryoda oynatma_listesi yok.")
        return 1
    ana = next(y for y in sonuc["yuklenen"] if y["tur"] == "ana")
    uyarilar: list[str] = []
    if not youtube.listeye_ekle(ana["id"], liste, uyarilar):
        print("Eklenemedi:", uyarilar)
        return 1
    sonuc["uyarilar"] = [u for u in sonuc.get("uyarilar", []) if "oynatma listesine" not in u]
    sonuc["listede"] = True
    kayit.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{ana['id']} '{liste}' listesine eklendi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
