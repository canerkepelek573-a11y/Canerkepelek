"""Paralel üretilen parçaların ozet_*.json dosyalarını tek ozet.json'da birleştirir."""
import glob
import json
import sys

ad = sys.argv[1]
ozet = {"bolum": ad, "uyarilar": []}
for f in sorted(glob.glob(f"cikti/{ad}/ozet_*.json")):
    with open(f, encoding="utf-8") as g:
        d = json.load(g)
    ozet["uyarilar"] += d.pop("uyarilar", [])
    ozet.update({k: v for k, v in d.items() if k != "bolum"})
with open(f"cikti/{ad}/ozet.json", "w", encoding="utf-8") as g:
    json.dump(ozet, g, ensure_ascii=False, indent=1)
print(json.dumps(ozet, ensure_ascii=False, indent=1))
