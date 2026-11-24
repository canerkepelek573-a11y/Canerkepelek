"""YouTube'a yükleme (YouTube Data API v3).

Gerekli GitHub Secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
(denetim/izin rehberi: docs/youtube-api-denetim.md). Kapsamlar: youtube.upload + youtube.force-ssl.

Not: Google'ın denetiminden (audit) geçmemiş API projelerinin yüklediği videolar
"gizli" olarak kilitlenir. Denetim onaylanana kadar yükleme elle yapılır.
"""

from __future__ import annotations

import os
from pathlib import Path


def _servis():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    kimlik = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.force-ssl"],
    )
    return build("youtube", "v3", credentials=kimlik, cache_discovery=False)


def yukle(video: Path, baslik: str, aciklama: str, etiketler: list[str], gizlilik: str = "private",
          yayin_zamani: str | None = None, kapak: Path | None = None, altyazi: Path | None = None,
          yapay_zeka_beyani: bool = False, uyarilar: list[str] | None = None) -> str:
    """Videoyu yükler ve video kimliğini döndürür. Başarısızlıkta hata verir (sessiz geçmez)."""
    from googleapiclient.http import MediaFileUpload

    yt = _servis()
    durum = {"privacyStatus": gizlilik, "selfDeclaredMadeForKids": False,
             "containsSyntheticMedia": yapay_zeka_beyani}
    if yayin_zamani:
        durum.update(privacyStatus="private", publishAt=yayin_zamani)
    istek = yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": baslik[:100], "description": aciklama[:5000], "tags": etiketler,
                          "categoryId": "27", "defaultLanguage": "tr", "defaultAudioLanguage": "tr"},
              "status": durum},
        media_body=MediaFileUpload(str(video), chunksize=16 * 1024 * 1024, resumable=True),
    )
    cevap = None
    while cevap is None:
        _, cevap = istek.next_chunk()
    video_id = cevap["id"]

    # Video yüklendikten sonra kapak/altyazı reddedilirse (ör. kanal telefonla doğrulanmamışsa özel kapak
    # yüklenemez) yükleme yarıda bırakılmaz: uyarı kaydedilir, kanal sahibine bildirilir.
    if kapak and kapak.exists():
        try:
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(kapak))).execute()
        except Exception as hata:  # noqa: BLE001
            _uyar(uyarilar, f"{video_id}: kapak yüklenemedi: {hata}")
    if altyazi and altyazi.exists():
        try:
            yt.captions().insert(
                part="snippet",
                body={"snippet": {"videoId": video_id, "language": "tr", "name": "Türkçe"}},
                media_body=MediaFileUpload(str(altyazi), mimetype="application/octet-stream"),
            ).execute()
        except Exception as hata:  # noqa: BLE001
            _uyar(uyarilar, f"{video_id}: altyazı yüklenemedi: {hata}")
    return video_id


def _uyar(uyarilar: list[str] | None, mesaj: str) -> None:
    print("UYARI:", mesaj[:400], flush=True)
    if uyarilar is not None:
        uyarilar.append(mesaj[:400])


def listeye_ekle(video_id: str, liste_adi: str, uyarilar: list[str] | None = None) -> str | None:
    """Videoyu kanaldaki adı verilen oynatma listesine ekler; liste yoksa herkese açık olarak oluşturur."""
    try:
        yt = _servis()
        liste_id = None
        sayfa = None
        while liste_id is None:
            cevap = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=sayfa).execute()
            liste_id = next((o["id"] for o in cevap.get("items", [])
                             if o["snippet"]["title"].strip().casefold() == liste_adi.strip().casefold()), None)
            sayfa = cevap.get("nextPageToken")
            if not sayfa:
                break
        if liste_id is None:
            liste_id = yt.playlists().insert(
                part="snippet,status",
                body={"snippet": {"title": liste_adi, "defaultLanguage": "tr"},
                      "status": {"privacyStatus": "public"}},
            ).execute()["id"]
        yt.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": liste_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
        ).execute()
        return liste_id
    except Exception as hata:  # noqa: BLE001
        _uyar(uyarilar, f"{video_id}: oynatma listesine eklenemedi ({liste_adi}): {hata}")
        return None


def dogrula(video_id: str, gizlilik: str, yayin_zamani: str | None = None) -> bool:
    """Yüklemenin gerçekten istenen durumda olduğunu doğrular (temizlikten önce çağrılır).

    Video yüklenmiş olsa bile YouTube onu gizliye kilitlediyse (denetlenmemiş API projesi) ya da
    zamanlama kaybolduysa doğrulama geçmez; böylece üretim dosyaları silinmez.
    """
    cevap = _servis().videos().list(part="status", id=video_id).execute()
    ogeler = cevap.get("items", [])
    if not ogeler:
        return False
    durum = ogeler[0]["status"]
    if durum.get("uploadStatus") not in ("uploaded", "processed"):
        return False
    if yayin_zamani:                     # zamanlanmış: yayına kadar gizli + yayın zamanı duruyor olmalı
        return durum.get("privacyStatus") == "private" and bool(durum.get("publishAt"))
    return durum.get("privacyStatus") == gizlilik
