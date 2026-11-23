"""Örnek alınan kanalın (Gerçeği Bul) anlatım analizi için veri toplar.

GitHub Actions üzerinde çalışır (YouTube'a oradan erişilebiliyor).
Toplananlar yalnızca iç analiz içindir; analiz bitince ham metinler depodan silinir.

Çıktılar (analiz/ klasörü):
  videolar.tsv      : tüm videolar (izlenme, süre, başlık)
  shorts.tsv        : Shorts listesi
  metin/<id>.txt    : seçilen videoların otomatik altyazısından düz metin
  kapak/<id>.jpg    : seçilen videoların kapak fotoğrafları
  detay/<id>.txt    : açıklama, etiketler, bölümler
"""

import json
import re
import sys
from pathlib import Path

import yt_dlp

KANAL = "https://www.youtube.com/@gercegibul"
CIKTI = Path(__file__).resolve().parent.parent / "analiz"
EN_POPULER = 6
EN_YENI = 3


def liste(url: str) -> list[dict]:
    ayar = {"extract_flat": "in_playlist", "quiet": True, "skip_download": True, "ignoreerrors": True}
    with yt_dlp.YoutubeDL(ayar) as ydl:
        bilgi = ydl.extract_info(url, download=False) or {}
    return [e for e in (bilgi.get("entries") or []) if e]


def tsv_yaz(dosya: Path, videolar: list[dict]) -> None:
    satirlar = ["izlenme\tsure_dk\tid\tbaslik"]
    for v in videolar:
        sure = v.get("duration")
        satirlar.append(
            f'{v.get("view_count") or ""}\t{round(sure / 60, 1) if sure else ""}\t{v.get("id")}\t{v.get("title")}'
        )
    dosya.write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def vtt_duz_metin(vtt: str) -> str:
    """Otomatik altyazıdaki tekrar eden kayan satırları temizleyip düz metne çevirir."""
    satirlar, onceki = [], ""
    for satir in vtt.splitlines():
        if "-->" in satir or not satir.strip() or satir.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        temiz = re.sub(r"<[^>]+>", "", satir).strip()
        if temiz and temiz != onceki:
            satirlar.append(temiz)
            onceki = temiz
    # ardışık satırlar arasındaki kelime örtüşmelerini at (kayan altyazı tekrarları)
    kelimeler: list[str] = []
    for s in satirlar:
        yeni = s.split()
        ortusme = 0
        for n in range(min(len(kelimeler), len(yeni)), 0, -1):
            if kelimeler[-n:] == yeni[:n]:
                ortusme = n
                break
        kelimeler.extend(yeni[ortusme:])
    return " ".join(kelimeler)


def detay_indir(video_id: str) -> None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ayar = {
        "quiet": True,
        "skip_download": True,
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": ["tr", "tr-orig", "tr.*"],
        "subtitlesformat": "vtt",
        "writethumbnail": True,
        "postprocessors": [{"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"}],
        "outtmpl": str(CIKTI / "gecici" / "%(id)s.%(ext)s"),
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ayar) as ydl:
        bilgi = ydl.extract_info(url, download=True)
    if not bilgi:
        print(f"HATA: {video_id} bilgisi alınamadı")
        return

    bolumler = "\n".join(
        f'{int(b["start_time"]) // 60:02d}:{int(b["start_time"]) % 60:02d} {b["title"]}'
        for b in (bilgi.get("chapters") or [])
    )
    (CIKTI / "detay" / f"{video_id}.txt").write_text(
        f'BAŞLIK: {bilgi.get("title")}\n'
        f'İZLENME: {bilgi.get("view_count")}  BEĞENİ: {bilgi.get("like_count")}  '
        f'YORUM: {bilgi.get("comment_count")}  SÜRE: {bilgi.get("duration")} sn\n'
        f'YÜKLEME: {bilgi.get("upload_date")}\n'
        f'ETİKETLER: {", ".join(bilgi.get("tags") or [])}\n\n'
        f'BÖLÜMLER:\n{bolumler}\n\n'
        f'AÇIKLAMA:\n{bilgi.get("description")}\n',
        encoding="utf-8",
    )

    gecici = CIKTI / "gecici"
    for vtt in sorted(gecici.glob(f"{video_id}*.vtt")):
        (CIKTI / "metin" / f"{video_id}.txt").write_text(
            vtt_duz_metin(vtt.read_text(encoding="utf-8")), encoding="utf-8"
        )
        break
    else:
        print(f"UYARI: {video_id} için Türkçe altyazı bulunamadı")
    for resim in gecici.glob(f"{video_id}.*"):
        if resim.suffix in (".jpg", ".webp", ".png"):
            resim.rename(CIKTI / "kapak" / f"{video_id}{resim.suffix}")


def main() -> int:
    for klasor in ("metin", "kapak", "detay", "gecici"):
        (CIKTI / klasor).mkdir(parents=True, exist_ok=True)

    videolar = liste(f"{KANAL}/videos")
    shorts = liste(f"{KANAL}/shorts")
    print(f"{len(videolar)} video, {len(shorts)} Shorts bulundu")
    if not videolar and not shorts:
        print("HATA: kanal listesi alınamadı")
        return 1
    tsv_yaz(CIKTI / "videolar.tsv", videolar)
    tsv_yaz(CIKTI / "shorts.tsv", shorts)

    populer = sorted(videolar, key=lambda v: v.get("view_count") or 0, reverse=True)[:EN_POPULER]
    secilen = list(dict.fromkeys([v["id"] for v in populer] + [v["id"] for v in videolar[:EN_YENI]]))
    secilen += [s["id"] for s in sorted(shorts, key=lambda v: v.get("view_count") or 0, reverse=True)[:3]]
    for vid in secilen:
        try:
            detay_indir(vid)
        except Exception as hata:
            print(f"HATA: {vid} — {hata}")

    for dosya in (CIKTI / "gecici").glob("*"):
        dosya.unlink()
    (CIKTI / "gecici").rmdir()
    (CIKTI / "secilen.json").write_text(json.dumps(secilen, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
