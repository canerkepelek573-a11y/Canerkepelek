# YouTube API Denetimi (Audit) — Telefondan Adım Adım Rehber

Hazırlanma: 24 Kasım 2026 · Araç: "Derin Gizem Yükleyici" (Google Cloud OAuth uygulaması) · Kanal: Gerçek Gizem

Bu rehber, YouTube'a GitHub Actions üzerinden yüklenen videoların **herkese açık / zamanlanmış** yayınlanabilmesi
için gereken "YouTube API Services – Audit and Quota Extension" (denetim ve kota artırma) başvurusunu anlatır.
Tüm adımlar telefondan yapılabilir. Formdaki her alan için **kopyala-yapıştır hazır İngilizce cevaplar** 5. bölümdedir.

> Bu dosyada hiçbir kişisel bilgi, e-posta, istemci kimliği (client ID) veya gizli anahtar yoktur.
> `<KANAL_URL>`, `<PROJE_NUMARASI>` gibi yer tutucuları kendi bilginizle değiştirin. Gizli anahtarları
> (client secret, refresh token) **hiçbir forma, sohbete veya e-postaya yazmayın**; Google bunları istemez.

---

## ÖNEMLİ GÜNCELLEME — Önce bunu okuyun (2 Kasım 2026 değişikliği)

Google, YouTube Data API **Revision History** sayfasında **2 Kasım 2026** tarihli bir duyuru yayımladı:
doğrulanmamış (denetlenmemiş) API projelerinden `videos.insert` ile yüklenen videolar **artık "gizli" moda
kilitlenmiyor**. 28 Temmuz 2020'den beri geçerli olan kural kaldırıldı. `videos.insert` başvuru sayfası da artık
"Videos uploaded from unverified API projects are not restricted to private viewing mode" diyor.

**Bunun anlamı:** Büyük ihtimalle denetime **hiç gerek kalmadı**. Bizim yükleme düzenimiz (bölüm başına 5 video,
günde 100 yükleme olan varsayılan kotanın çok altında) için kota artırmaya da gerek yok.

Bu yüzden sıra şöyle:
1. **Adım 0'daki test yüklemesini yapın.** Video kilitlenmezse denetim başvurusuna gerek yok; burada durun.
2. Test videosu yine de "gizli olarak kilitlendi" olursa (veya ileride kota artırmak gerekirse) Adım 1'den
   itibaren denetim başvurusunu yapın.

> Not: Google'ın sayfaları bu değişiklik konusunda bir süre tutarsız göründü (bazı eski/önbellek kopyalarda 2020
> kuralı hâlâ yazıyor). Kesin karar, kendi kanalımızda yapılacak test yüklemesine göre verilmelidir.

---

## Adım 0 — Test yüklemesi: Videolar hâlâ kilitleniyor mu? (5 dakika)

Mevcut iş akışları gerçek bölümü yükleyip ardından üretim dosyalarını siliyor (CLAUDE.md §7). Test için gerçek
bölümü kullanmayın. Sohbette Claude'dan şunu isteyin:

> "Kısa bir test videosunu **liste dışı (unlisted)** olarak yükleyen ve YouTube'un uyguladığı gizlilik
> durumunu yazan bir test iş akışı hazırla."

Sonra telefondan:
1. GitHub → depo → **Actions** → test iş akışı → **Run workflow**.
2. Bittikten sonra **YouTube Studio** uygulaması → **İçerik** → test videosu.
3. Kontrol edin:
   - Video **"Liste dışı"** görünüyorsa → kilit yok. **Denetime gerek yok.** Test videosunu Studio'dan siz silin.
   - Video **"Gizli"** ve yanında kilit/uyarı varsa, ya da "Videonuz gizli olarak kilitlendi" konulu bir e-posta
     geldiyse → kilit hâlâ geçerli. **Adım 1'e geçin.** (Kilitlenen videolar için itiraz yapılamaz; o video
     ya Studio'dan elle ya da denetim onaylandıktan sonra API ile yeniden yüklenir.)

---

## Adım 1 — Hazırlık kontrol listesi

| # | Gereken şey | Durum / nereden |
|---|---|---|
| 1 | Google Cloud **proje numarası** (Project number, rakamlardan oluşur; "Project ID" değil) | Cloud Console → proje adı → "Project info" kartı |
| 2 | OAuth uygulamasının adı: **Derin Gizem Yükleyici** (formda aynen bu ad yazılır) | Cloud Console → Google Auth Platform → Branding |
| 3 | **Herkese açık gizlilik politikası adresi** (`<GIZLILIK_URL>`) | Adım 2 |
| 4 | Kanal adresi (`<KANAL_URL>`) | YouTube uygulaması → Kanalınız → Paylaş → Bağlantıyı kopyala |
| 5 | İletişim e-postası (`<ILETISIM_EPOSTA>`) | Kanalın bağlı olduğu Google hesabı önerilir |
| 6 | Kısa ekran kaydı (demo, 1–3 dk), YouTube'da **liste dışı** | Adım 3 |
| 7 | 3–4 ekran görüntüsü (iş akışı ekranı, yükleme adımı kaydı, Studio'da video) | Adım 3 |
| 8 | 5. bölümdeki İngilizce cevaplar | Bu dosya |

**Telefon ipucu:** Google Cloud Console mobilde dar görünür. Chrome'da sağ üstteki **⋮ → "Masaüstü sitesi"**
seçeneğini açın. Denetim formu (support.google.com) mobilde normal çalışır.

---

## Adım 2 — Gizlilik politikasını herkese açık bir adrese koyun

Denetçiler, API istemcisinin **herkesin açabileceği** bir gizlilik politikası olup olmadığına ve bu politikanın
YouTube Developer Policies (III.A.2) maddelerini karşılayıp karşılamadığına bakar. Depomuz **özel (private)**
olduğu için `docs/gizlilik-politikasi.md` dışarıdan açılmaz. Bu yüzden ayrı ve herkese açık bir adres gerekir.

**Kolay yollar (birini seçin):**
- **A (önerilen):** Claude'dan, içinde yalnızca gizlilik politikası olan ayrı bir **herkese açık** GitHub deposu
  ve GitHub Pages sayfası hazırlamasını isteyin. Adres `https://<KULLANICI>.github.io/<DEPO>/` biçiminde olur.
- **B:** Google Dokümanlar'da aşağıdaki metni yapıştırın → Paylaş → "Bağlantıya sahip olan herkes – Görüntüleyen".

Politika **İngilizce** olmalı (denetçiler İngilizce okur; altına Türkçesi de eklenebilir). Mevcut Türkçe
politikada III.A.2 için eksik olan şunlar aşağıdaki metne eklendi: "YouTube API Services kullanır" ifadesi, YouTube
ToS'a bağlılık cümlesi, erişimi kaldırma bağlantısı (Google güvenlik ayarları), iletişim adresi, çerez bilgisi,
saklama süresi.

### Yapıştırılacak İngilizce gizlilik politikası

```text
Privacy Policy — Derin Gizem Yükleyici
Last updated: <TARIH>

"Derin Gizem Yükleyici" (the "Tool") is a private, internal upload tool operated by the owner of the
YouTube channel "Gerçek Gizem" (<KANAL_URL>). It is used only by the channel owner to upload the owner's
own videos to the owner's own YouTube channel. It has no other users and is not offered to the public.

1. Use of YouTube API Services
The Tool uses YouTube API Services. By using the Tool, you agree to be bound by the YouTube Terms of
Service: https://www.youtube.com/t/terms
Google Privacy Policy: https://policies.google.com/privacy

2. What data the Tool accesses
With the channel owner's OAuth authorization (scopes youtube.upload and youtube.force-ssl), the Tool:
- uploads the owner's own video files with their title, description, tags, category, language,
  privacy status / scheduled publish time and AI-disclosure flag (videos.insert);
- sets a custom thumbnail on those videos (thumbnails.set);
- uploads a Turkish caption file to those videos (captions.insert);
- reads the processing/upload status of the videos it has just uploaded (videos.list);
- for a one-time connection test, reads the owner's own channel title and public statistics
  (channels.list, mine=true). These values are only printed in the run log and are not stored elsewhere.
The Tool does not access any other user's data, comments, subscribers, analytics or private information.

3. How data is used, stored and shared
- The uploaded content is the owner's own content and is published on YouTube.
- OAuth credentials (client ID, client secret, refresh token) are stored only as encrypted GitHub
  Actions secrets in the owner's private repository. They never appear in code or logs.
- After a successful upload, the Tool keeps only a small upload log (the YouTube video IDs and
  scheduled publish times of the owner's own uploads) in the owner's private repository. No other
  YouTube API data is stored. Temporary production files are deleted after the upload is verified.
- No data is sold, shared with third parties, used for advertising, or combined with other data.
- The Tool does not use cookies and does not collect device information; it has no website or app
  front end. It runs only as an automated job started by the owner.

4. Revoking access and deleting data
The owner can revoke the Tool's access at any time via the Google security settings page:
https://myaccount.google.com/permissions
After access is revoked, stored credentials are deleted from the repository secrets. The owner can
request deletion of the upload log at any time; it is deleted within 7 days.

5. Contact
<ILETISIM_EPOSTA>
```

> Yayınladıktan sonra adresi telefonda gizli sekmede (giriş yapmadan) açıp herkese açık olduğunu kontrol edin.
> Kod veya kapsamlar değişirse politika da güncellenir. Denetçiler politika ile kodun farklı olmasını sık yakalar.

---

## Adım 3 — Demo ekran kaydı ve ekran görüntüleri

**Zorunlu mu?** YouTube'un denetim formunda demo videonun zorunlu olduğuna dair resmî bir kaynak bulunamadı.
Ancak herkese açık olmayan (internal) araçlarda denetçinin aracı başka türlü göremediği için üçüncü taraf
kaynaklar ekran kaydı / ekran görüntüsü eklemeyi öneriyor ve denetçiler bunu sık istiyor. **Hazırlayın ve
forma bağlantısını ekleyin.** (Ayrı bir süreç olan OAuth uygulama doğrulamasında ise demo video **zorunludur**,
bkz. Adım 7.)

**Telefonla çekim (1–3 dakika, sessiz olabilir):**
- Android: bildirim panelini aşağı çekin → **Ekran kaydı**. iPhone: Denetim Merkezi → **Ekran Kaydı**.

**Çekim senaryosu (sırayla gösterin):**
1. GitHub deposunun **Actions** sekmesi → "Hazır bölümü topla / yükle" iş akışı → **Run workflow**
   ekranı (yükleme seçeneği seçiliyken).
2. Çalışmanın **"YouTube'a yükle"** adımının kaydı: "Ana video yüklendi…", "Shorts yüklendi…",
   "Yükleme doğrulandı" satırları.
3. **YouTube Studio** → İçerik: yüklenen videolar, başlık/açıklama, kapak ve **Altyazılar** bölümünde Türkçe altyazı.
4. Google hesabı → **Güvenlik → Üçüncü taraf bağlantıları** sayfasında "Derin Gizem Yükleyici" ve
   "Erişimi kaldır" düğmesinin yeri (dokunmayın, sadece gösterin).

**Dikkat:** GitHub'ın **Settings → Secrets** sayfasını açmayın. Hiçbir anahtar, e-posta veya client ID
görünmemeli. Kaydı YouTube'a **liste dışı** yükleyin ve bağlantısını `<DEMO_VIDEO_URL>` olarak kullanın.
Aynı ekranlardan 3–4 ekran görüntüsü alın (formdaki dosya yükleme alanı için).

---

## Adım 4 — Formu açın

**Form adresi (resmî):** https://support.google.com/youtube/contact/yt_api_form

- Formu, API projesinin sahibi olan **ve kanalın bağlı olduğu** Google hesabıyla açın.
- Daha önce denetimden geçtiyseniz (son 12 ay) kısa form kullanılır:
  https://support.google.com/youtube/contact/yt_api_audited_developer_requests_form
- Denetim reddedilirse itiraz formu "Quota and Compliance Audits" sayfasında listelenir.

> Formun alan adları zaman zaman değişir. Aşağıdaki liste formun bilinen yapısına göre hazırlandı. Formda
> farklı bir soru çıkarsa en yakın İngilizce cevabı kullanın; her cevap 5. bölümde parça parça hazır.

---

## Adım 5 — Form alanları ve hazır İngilizce cevaplar

### 5.1 Başvuru nedeni (Reason for filling out this form)
Seçenekler arasından **denetim / uyum denetimi (audit)** olanı seçin. "Unverified project uploads restricted to
private" gibi bir seçenek varsa onu seçin. Kota artırma **istemiyoruz**; kota sorulursa "no additional quota"
deyin.

**Ek açıklama alanı için:**
```text
We are requesting a compliance audit for our internal upload tool so that videos uploaded via
videos.insert are not locked as private. We do NOT need additional quota; our usage is far below the
default allocation (about 5 videos.insert calls and about 460 other units per release day).
```

### 5.2 İletişim ve kuruluş bilgileri (Contact / Organization)
| Alan | Ne yazılır |
|---|---|
| Name | `<AD_SOYAD>` |
| Email | `<ILETISIM_EPOSTA>` |
| Organization / Company name | `Gerçek Gizem (individual YouTube creator)`. Şirket yoksa bireysel olduğunuzu yazın. |
| Organization website | `<KANAL_URL>`. Ayrı bir web sitesi yoksa kanal adresi yeterli. |
| Country / Address | `Türkiye`, adres istenirse `<ADRES>` |

### 5.3 API istemcisi (API Client) bilgileri
| Alan | Cevap |
|---|---|
| Google Cloud project number | `<PROJE_NUMARASI>` |
| API client name | `Derin Gizem Yükleyici` |
| Is the API client publicly available or internal? | **Internal / private (not publicly available)** |
| API client URL / link | `Not applicable – internal automation with no public website or app. Demo: <DEMO_VIDEO_URL>` |
| Privacy policy URL | `<GIZLILIK_URL>` |
| Terms of service URL (istenirse) | `Not applicable – single-user internal tool; the privacy policy states that use is bound by the YouTube Terms of Service.` |
| YouTube API services used | **YouTube Data API v3** (yalnızca bu; Analytics/Reporting/Embedded Player/Live **yok**) |
| Primary audience | `Internal use only – the channel owner (one person).` |
| Number of users | `1` |
| Do users sign in with Google/YouTube (OAuth)? | `Yes – only the channel owner, once, to authorize the tool for their own channel.` |
| Does the client display YouTube data to others? | `No.` |
| Does it create reports / metrics / analytics? | `No.` |
| Does it combine YouTube data with other platforms? | `No.` |
| Data storage period | `Only video IDs of the owner's own uploads are kept as an upload log; no other API data is stored (see answer below).` |

### 5.4 Uygulama açıklaması (App description / Use case)
```text
"Derin Gizem Yükleyici" is a private, internal automation tool used only by the owner of the YouTube
channel "Gerçek Gizem" (<KANAL_URL>), an educational Turkish documentary channel about ancient mysteries,
lost civilizations and unsolved cases. The owner prepares each episode (one main video of 20+ minutes,
four Shorts, a thumbnail and a Turkish caption file) and starts a GitHub Actions job in the owner's
private GitHub repository. The job uses the YouTube Data API v3 with the owner's own OAuth authorization
to upload these videos to the owner's own channel, set the custom thumbnail, add the Turkish caption
track and schedule publishing (publishAt) at 19:00 Turkey time. It then reads the upload status of the
videos it just uploaded to confirm the upload succeeded.

The tool has exactly one user (the channel owner) and operates on exactly one channel (the owner's own).
It has no public website, no app store listing and no other users, and it never accesses other
users' data. It does not read comments, analytics, subscribers or any third-party content.
```

### 5.5 Çağrılan API yöntemleri ve nedenleri (API methods and why)
```text
All calls use the YouTube Data API v3 and act only on the owner's own channel and videos:

1. videos.insert (part=snippet,status), resumable upload
   Uploads the owner's video file with title, description, tags, categoryId 27 (Education),
   defaultLanguage/defaultAudioLanguage "tr", status.privacyStatus (or private + status.publishAt
   for scheduled publishing), selfDeclaredMadeForKids=false and status.containsSyntheticMedia
   (altered/synthetic content disclosure). About 5 calls per episode (1 main video + 4 Shorts).

2. thumbnails.set
   Sets the custom thumbnail for the main video. 1 call per episode.

3. captions.insert (part=snippet)
   Uploads the Turkish caption track (SRT) for the main video, for accessibility. 1 call per episode.

4. videos.list (part=status,processingDetails, id=<the IDs just uploaded>)
   Confirms that each upload completed before temporary production files are deleted.
   About 5 calls per episode.

5. channels.list (part=snippet,statistics, mine=true)
   Used only in a manual one-time connection test to confirm the authorization points to the
   correct channel. The result is only printed in the private job log and is not stored.

No other methods are called. The tool never deletes, edits or reads other users' videos, comments,
playlists or subscriptions.

Estimated usage per episode: 5 calls in the Video Uploads bucket (default limit 100/day) and about
460 units in the general bucket (thumbnails.set 50 + captions.insert 400 + reads ~6), far below the
default 10,000 units/day. Episodes are released about once a week.
```

### 5.6 OAuth kapsamları (Scopes) gerekçesi
```text
- https://www.googleapis.com/auth/youtube.upload: required for videos.insert and thumbnails.set.
- https://www.googleapis.com/auth/youtube.force-ssl: required for captions.insert (Turkish caption
  upload) and used for videos.list / channels.list on the owner's own channel.
Both scopes are granted only by the channel owner for the owner's own channel. If preferred, we can
reduce the request to youtube.force-ssl alone, which also covers uploads.
```

### 5.7 Veri işleme, saklama ve silme (Data handling, storage, deletion)
```text
- Credentials: the OAuth client ID, client secret and refresh token are stored only as encrypted
  GitHub Actions secrets in the owner's private repository. They are injected as environment
  variables at run time and are never written to code, files or logs.
- YouTube API data stored: only the video IDs and scheduled publish times of the owner's own uploads
  are kept in a small upload log file in the owner's private repository, so the owner can track which
  episodes were uploaded. No video statistics, comments, analytics, other channels' data or personal
  data are stored. channels.list output from the one-time connection test is only shown in the job log.
- Temporary files (rendered videos, thumbnails, captions) are deleted automatically once the upload is
  verified with videos.list.
- Sharing: no YouTube API data is sold, shared with third parties, used for advertising, or combined
  with data from other platforms.
- Revocation: the owner can revoke access at any time at https://myaccount.google.com/permissions;
  the stored credentials are then deleted from the repository secrets, and the upload log can be
  deleted on request.
```

### 5.8 Kullanıcı sayısı (Number of users / channels)
```text
1 user (the channel owner) and 1 channel (the owner's own channel "Gerçek Gizem", <KANAL_URL>).
The tool is not offered to anyone else and will not onboard other users.
```

### 5.9 Kurallara uyum beyanı (Compliance with YouTube API ToS and Developer Policies)
```text
We have read and comply with the YouTube API Services Terms of Service and Developer Policies:
- The tool only acts on the authorizing user's own channel with that user's explicit OAuth consent.
- It requests only the scopes it needs and calls only the methods listed above.
- A public privacy policy (<GIZLILIK_URL>) states that the tool uses YouTube API Services, links to the
  YouTube Terms of Service and the Google Privacy Policy, explains what data is accessed, stored and
  shared, and explains how to revoke access via the Google security settings page.
- No YouTube API data is sold, shared, aggregated across channels, or used to build derived metrics.
- Uploaded content is the owner's original educational content; synthetic/altered content is disclosed
  through status.containsSyntheticMedia where applicable, and videos are not made for kids.
- The tool does not manipulate engagement, does not spam and does not upload on behalf of others.
```

### 5.10 Test hesabı / demo (Test account or demo)
```text
The tool has no user interface or login page that a reviewer could access; it runs only as a private
GitHub Actions job owned by the channel owner. A screen recording showing the full flow (starting the
job, the upload log, and the uploaded video with thumbnail and captions in YouTube Studio) is
available here: <DEMO_VIDEO_URL>. Screenshots are attached. We are happy to answer any questions or
provide additional recordings.
```

### 5.11 Dosya ekleri (Upload documents / screenshots)
Adım 3'teki 3–4 ekran görüntüsünü ekleyin. Gizlilik politikasının ekran görüntüsü de eklenebilir.
Formu gönderin ve gelen onay e-postasını silmeyin.

---

## Adım 6 — Gönderdikten sonra

- Cevap, formdaki e-posta adresine **YouTube API Services ekibinden** gelir. Ek soru gelirse **aynı e-posta
  zincirinde** yanıtlayın, yeni form açmayın. Ek soruları sohbete yapıştırırsanız Claude cevap taslağı hazırlar.
- **Süre:** Google resmî bir süre açıklamıyor. Geliştirici deneyimleri **yaklaşık 1 hafta ile birkaç hafta**
  arasında. Ek soru gelirse daha uzun sürebilir. 2–3 hafta cevap gelmezse aynı e-postaya kısa bir hatırlatma yazın.
- Bekleme süresince: Yüklemeler **elle** (YouTube Studio uygulamasından) yapılabilir; elle yüklenen videolar kilitlenmez.
- Onay geldikten sonra kilit **yeni** yüklemeler için kalkar. Daha önce kilitlenmiş videolar açılmaz; yeniden yüklenir.
- Denetim periyodiktir: Google ileride yeniden uyum denetimi isteyebilir. Kod veya kapsam değişirse politika
  güncel tutulur.

---

## Adım 6.1 — Sık reddedilme nedenleri ve önlemleri

| Neden | Bizdeki önlem |
|---|---|
| Gizlilik politikası açılmıyor / özel depoda / III.A.2 maddeleri eksik | Adım 2: herkese açık, İngilizce, tüm maddeler var |
| Politika ile kodun yaptığı şey farklı (ör. istatistik okuma yazılmamış) | Politikada `channels.list` testi ve upload log'u açıkça yazıldı |
| Kullanım amacı belirsiz ("for my project" gibi) | 5.4–5.5'te yöntem yöntem gerekçe |
| Gereksiz kapsam istemek | 5.6'da gerekçe; gerekirse yalnız `youtube.force-ssl`e inilebilir |
| API verisini süresiz saklama / üçüncü kişilerle paylaşma | Yalnızca kendi video ID'lerimiz; paylaşım yok |
| Denetçinin aracı görememesi | Demo kaydı + ekran görüntüleri (5.10) |
| Formdaki uygulama adı ile OAuth onay ekranındaki adın farklı olması | Her yerde **"Derin Gizem Yükleyici"** yazılır |
| E-posta ile gelen ek sorulara cevap verilmemesi | E-postayı takip edin; sorulara aynı zincirde cevap verin |

---

## Adım 7 — OAuth uygulama doğrulaması (ayrı süreç): Gerekli mi?

YouTube API denetimi ile Google'ın **OAuth uygulama doğrulaması** (Google Auth Platform → Verification)
**ayrı süreçlerdir**.

- `youtube.upload` ve `youtube.force-ssl` **hassas (sensitive)** kapsamlardır, kısıtlı (restricted) değildir.
- Google'a göre **kişisel kullanım / 100'den az kullanıcı** için doğrulanmamış uygulama çalışmaya devam eder.
  Tek fark, yetki verirken bir kez görülen **"Google bu uygulamayı doğrulamadı"** uyarısıdır.
  (**Gelişmiş → Derin Gizem Yükleyici'ye git** ile geçilir.) Tek kullanıcılı aracımız için **OAuth
  doğrulaması gerekmez**.
- OAuth doğrulaması yapılmak istenirse (veya denetçi isterse) şunlar gerekir: Search Console'da doğrulanmış
  bir alan adı, o alan adında ana sayfa ve gizlilik politikası, her kapsamın gerekçesi ve onay ekranını gösteren
  **zorunlu demo video**. Bu ağır bir süreçtir; yalnızca istenirse yapılır.

**"Testing" (Test) modu konusunda uyarı:** Uygulama **"In production" (Üretimde)** kalmalı.
- Yayın durumu **Testing** olan harici (External) uygulamalarda test kullanıcısının **refresh token'ı 7 gün
  sonra geçersiz olur** (yalnızca ad/e-posta/profil kapsamları istenirse bu kural uygulanmaz; bizde uygulanır).
  Her hafta yeniden yetki vermek gerekir ve GitHub Actions'taki yükleme bozulur.
- Testing modu denetim sonucunu değiştirmez; denetim **API projesine** bağlıdır, uygulamanın yayın durumuna değil.
- Refresh token uygulama **Testing** iken alındıysa "In production"a geçtikten sonra da 7 günde düşebilir.
  Bu durumda token yeniden alınır ve GitHub Secrets'taki `YT_REFRESH_TOKEN` güncellenir.
- Üretimdeki token'lar da 6 ay hiç kullanılmazsa veya erişim kaldırılırsa geçersiz olur.

---

## Adım 8 — Onaydan (veya kilit olmadığı görüldükten) sonra

1. Bölümü normal şekilde yükleyin ("Hazır bölümü topla / yükle" → `yukle: public` veya zamanlı yayın).
2. İlk gerçek yüklemeden sonra YouTube Studio'da videoların **zamanlanmış/herkese açık** göründüğünü kontrol edin.
3. CLAUDE.md §5.11 hatırlatması: sabitlenmiş yorum ve bitiş ekranı elle eklenir.

---

## Kaynaklar

- YouTube Data API – Revision History (2 Kasım 2026: doğrulanmamış projelerden yüklemeler artık gizliye
  kilitlenmiyor; 1 Haziran 2026: `videos.insert` için ayrı kota kovası):
  https://developers.google.com/youtube/data/revision_history
- Videos: insert (kota maliyeti, gizlilik varsayılanı, doğrulanmamış projeler notu):
  https://developers.google.com/youtube/v3/docs/videos/insert
- Quota and Compliance Audits (denetim süreci, formlar, itiraz):
  https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- YouTube API Services – Audit and Quota Extension Form: https://support.google.com/youtube/contact/yt_api_form
- Denetlenmiş geliştirici kısa formu: https://support.google.com/youtube/contact/yt_api_audited_developer_requests_form
- YouTube API Services – Developer Policies (III.A.2 gizlilik politikası, veri saklama):
  https://developers.google.com/youtube/terms/developer-policies
- Videos locked as private (YouTube Yardım): https://support.google.com/youtube/answer/7300965
- Unverified apps (100 kullanıcı sınırı, kişisel kullanım): https://support.google.com/cloud/answer/7454865
- Sensitive scope verification: https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
- OAuth doğrulaması demo video kuralları: https://support.google.com/cloud/answer/13804565
- Testing modunda 7 günlük refresh token (Google'ın OAuth 2.0 belgesinin "Refresh token expiration" bölümünü
  aktaran Google Ads API forum yanıtları): https://groups.google.com/g/adwords-api/c/Z_kihrf6VCE
- Denetim süresi ve kilit deneyimleri (geliştirici raporları): https://github.com/tokland/youtube-upload/issues/306
- Denetimde politika–kod uyumu ve iptal (revoke) gereklilikleri (örnek proje): https://github.com/gyuv/youtube-ai-agent/pull/3

> Doğrulama notu: Google'ın sayfaları bu çalışma ortamından doğrudan açılamadı. Bilgiler arama sonuçlarındaki
> Google sayfa özetlerinden ve üçüncü taraf kaynaklardan derlendi. Formun alan adları birebir doğrulanamadı.
