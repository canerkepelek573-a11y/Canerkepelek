"""Yüklenen videoların YouTube'daki durumunu yazdırır (gizlilik, zamanlama, işlenme, kilit)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from derin.youtube import _servis  # noqa: E402


def main() -> int:
    kayit = json.loads((Path(sys.argv[1]) / "yuklendi.json").read_text(encoding="utf-8"))
    kimlikler = [y["id"] for y in kayit["yuklenen"]]
    cevap = _servis().videos().list(part="status,processingDetails,snippet", id=",".join(kimlikler)).execute()
    for o in cevap.get("items", []):
        d = o["status"]
        print(f"{o['id']} | {o['snippet']['title'][:50]} | gizlilik={d.get('privacyStatus')} "
              f"yayin={d.get('publishAt')} yukleme={d.get('uploadStatus')} "
              f"ret={d.get('rejectionReason')} hata={d.get('failureReason')} "
              f"islenme={o.get('processingDetails', {}).get('processingStatus')}")
    eksik = set(kimlikler) - {o["id"] for o in cevap.get("items", [])}
    if eksik:
        print("BULUNAMADI:", ", ".join(sorted(eksik)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
