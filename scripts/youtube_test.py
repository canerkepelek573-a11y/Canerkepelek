"""YouTube bağlantı testi: hiçbir şey yüklemez, yalnızca kanalın adını ve istatistiklerini okur."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from derin.youtube import _servis  # noqa: E402

cevap = _servis().channels().list(part="snippet,statistics", mine=True).execute()
ogeler = cevap.get("items", [])
if not ogeler:
    print("HATA: Bu hesaba bağlı bir YouTube kanalı bulunamadı.")
    sys.exit(1)
for k in ogeler:
    s = k["statistics"]
    print(f"KANAL: {k['snippet']['title']}")
    print(f"ABONE: {s.get('subscriberCount')}  VİDEO: {s.get('videoCount')}  İZLENME: {s.get('viewCount')}")
