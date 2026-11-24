"""Kanal sahibinin açık talimatıyla: yuklendi.json'daki videoları YouTube'dan kalıcı olarak siler ve doğrular.

Kullanım: python scripts/sil.py bolumler/001-dyatlov
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from derin.youtube import _servis  # noqa: E402


def main() -> int:
    bolum = Path(sys.argv[1])
    kayit = bolum / "yuklendi.json"
    veri = json.loads(kayit.read_text(encoding="utf-8"))
    kimlikler = [y["id"] for y in veri["yuklenen"]]
    yt = _servis()
    for vid in kimlikler:
        try:
            yt.videos().delete(id=vid).execute()
            print(f"Silindi: {vid}", flush=True)
        except Exception as hata:  # noqa: BLE001
            print(f"Silme hatası {vid}: {hata}", flush=True)
    kalan = [o["id"] for o in yt.videos().list(part="id", id=",".join(kimlikler)).execute().get("items", [])]
    if kalan:
        print("HATA: hâlâ kanalda duran videolar:", ", ".join(kalan))
        return 1
    veri["silindi"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (bolum / "silindi.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    kayit.unlink()
    print(f"{len(kimlikler)} videonun tamamı kanaldan silindi (doğrulandı).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
