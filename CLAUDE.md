# DERİN GİZEM — YouTube Kanalı Kural Dosyası

Bu dosya, "Derin Gizem" YouTube kanalı için yapılan tüm çalışmaların ana kural dosyasıdır.
Her oturumda önce bu dosya okunur ve buradaki kurallara **eksiksiz** uyulur.
Kurallar kanal sahibi tarafından belirlenmiştir; değişiklik yalnızca kanal sahibinin onayıyla yapılır.

Detaylı araştırma notları: `docs/arastirma-google-tts.md`, `docs/arastirma-seslendirme.md` ve `docs/arastirma-youtube.md`

---

## 1. Amaç

Her bölüm için şu paket eksiksiz üretilir:

| Çıktı | Özellik |
|---|---|
| **1 ana video** | En az **20 dakika**, yatay (16:9), en az 1080p |
| **4 Shorts** | Aynı konudan, dikey (9:16), her biri tek başına "vay be" dedirtecek |
| **Kapak fotoğrafları** | Ana video ve Shorts için |
| **Başlık, açıklama, etiketler, bölümler (zaman damgaları)** | Kanalı öne çıkaracak şekilde |

Videolar **çok ilgi çekecek**, izleyiciyi **sonuna kadar kanalda tutacak** şekilde hazırlanır.
Her iş **en dikkatli şekilde** yapılır; aceleye getirilmiş, özensiz çıktı yüklenmez.

## 2. İçerik ve Anlatım Kuralları

1. **İlk dakikalar her şeydir.** Videonun ilk dakikaları çok güçlü bir gizem uyandırmalı:
   izleyici "Bu videoda ne var acaba, devamında ne gelecek?" diye merak etmeli.
   - İlk 30 saniyede en çarpıcı soru / en ilginç an gösterilir, cevabı **hemen verilmez**.
   - Video boyunca açık uçlu merak noktaları (cevabı sonra gelecek sorular) bırakılır.
2. **Doğruluk dengesi:**
   - Bilgilerin %100 doğru olma zorunluluğu yoktur; söylentiler, iddialar ve efsaneler anlatılabilir.
   - Ancak **çok fazla yanlış bilgi içermez.** Bilinen gerçekler doğru aktarılır.
   - Hiçbir şey için "**%100 gerçektir**" denmez; hiçbir şey için "**%100 yalandır**" da denmez.
   - Söylentiler söylenti olarak sunulur: "iddiaya göre", "anlatılanlara göre", "söylentiye göre",
     "bazı araştırmacılara göre", "kimileri buna inanıyor, kimileri ise…" gibi ifadeler kullanılır.
   - Karar izleyiciye bırakılır; bu, yorum yapmayı ve etkileşimi artırır.
3. **Abone ol çağrıları:** Videonun belirli noktalarında ekranda "Abone Ol" butonu / yazısı tarzında
   görseller gösterilir (ilk 30 saniyede değil; izleyici merak noktasına bağlandıktan sonra,
   videonun ortalarında ve sona doğru). Shorts'ta sonda kısa bir çağrı yapılır.
4. Konu anlatımı sürükleyici, karanlık ve gizemli bir belgesel anlatıcısı tonunda olur.

## 3. Seslendirme Kuralları (Google Cloud Text-to-Speech)

1. Tüm seslendirme **Google Cloud Text-to-Speech** ile yapılır (kanal sahibinin kararı, 23.11.2026;
   önceki plan ElevenLabs idi, o araştırma `docs/arastirma-seslendirme.md` dosyasında referans olarak durur).
2. API anahtarı **asla** sohbete, koda veya depoya yazılmaz. GitHub'da
   **Settings → Secrets and variables → Actions** bölümüne `GOOGLE_CLOUD_API_KEY` adıyla eklenir.
3. **Yanlış seslendirme kesinlikle olmamalı.**
   - **Noktalama işaretlerine** kesinlikle dikkat edilir; cümleler doğru yerde durur, doğru vurguyla okunur.
   - **Sayılar kesik kesik okunmamalı.** Yıllar, tarihler, büyük sayılar, yüzdeler, ondalıklar,
     sıra sayıları ve Roma rakamları seslendirmeden önce **Türkçe yazıya çevrilir**
     (ör. `1947` → "bin dokuz yüz kırk yedi", `%40` → "yüzde kırk", `XIV.` → "On Dördüncü").
   - Yabancı özel isimlerin okunuşu kontrol edilir.
4. Üretilen ses **kontrol edilir** (yazıya geri çevrilip metinle karşılaştırılır);
   hatalı bölüm varsa o bölüm yeniden seslendirilir. Hatalı ses yüklenmez.
5. Seslendirme en iyi sonuç için araştırmaya dayalı ayarlarla yapılır (bkz. `docs/arastirma-google-tts.md`).
   Sayı çevirme, parçalara bölme ve kalite kontrol kuralları `docs/arastirma-seslendirme.md` dosyasında da geçerlidir.

## 3.1 Ses ve Görüntü Uyumu

Ses ve görüntü **net şekilde oturur** ve birbiriyle **tutarlı** olur:
1. **İçerik uyumu:** Ekranda o an anlatılan şey gösterilir. Anlatıcı bir mekândan, nesneden, tarihten
   veya kişiden bahsediyorsa görüntü de onunla ilgilidir; konuyla alakasız "dolgu" görüntü kullanılmaz.
2. **Zamanlama uyumu:** Görüntü geçişleri cümle ve paragraf sınırlarına denk gelir; bir cümlenin
   ortasında alakasız bir kesme yapılmaz. Görüntü süreleri seslendirmenin gerçek sürelerine göre hesaplanır
   (tahmini süreyle değil).
3. **Altyazı uyumu:** Altyazılar kelime kelime sesle eş zamanlı akar; sesten önce veya sonra görünmez.
   Altyazıda yazılan metin, seslendirmede okunan metinle birebir aynıdır (yabancı isimler orijinal yazımıyla).
4. **Efekt ve müzik uyumu:** Ses efektleri ve müzik vurguları görüntüdeki ana denk gelir; müzik
   anlatıcının sesini bastırmaz.
5. **Kontrol:** Her video yüklenmeden önce ses–görüntü–altyazı uyumu kontrol edilir.
   Kayma veya tutarsızlık varsa düzeltilmeden yüklenmez.

## 4. Başlık ve Kapak Fotoğrafı Kuralları

1. Bu konulardaki **en çok izlenen YouTube videoları** incelenir; başlık ve kapak fotoğrafı
   tarzları oradan öğrenilir (bkz. `docs/arastirma-youtube.md`).
2. Başlıklar ve kapaklar **kopyalanmaz**; daha **özgün** ve daha **kaliteli** hâle getirilir.
3. Merak uyandıran (clickbait) veya normal başlıklar kullanılabilir; ancak başlık ve kapak,
   videoda gerçekten olmayan bir şeyi vaat etmez (YouTube yanıltıcı içeriği cezalandırır).

## 5. Kanal Büyütme (YouTube'da Öne Çıkma)

Her adım kanalın büyümesine hizmet eder:
- Açıklamalar arama ve öneri sistemine uygun yazılır (anahtar kelimeler, bölümler/zaman damgaları, hashtag'ler).
- Shorts'lar ana videoya yönlendirir (ilgili video bağlantısı).
- Oynatma listeleri, sabitlenmiş yorum, bitiş ekranı kullanılır.
- Yükleme saati Türk izleyicinin aktif olduğu saatlere göre seçilir.

## 6. Telifsiz Görsel, Video ve Müzik

1. Kullanılan tüm video, fotoğraf ve müzikler **başımıza dert açmayacak şekilde telifsiz** kaynaklardan seçilir
   (ör. Pexels, Pixabay, Wikimedia Commons'ta kamu malı / CC0 olanlar, NASA gibi kamu kaynakları).
2. Lisansı belirsiz hiçbir materyal kullanılmaz.
3. Her video için kullanılan materyallerin kaynak ve lisans listesi tutulur.

## 7. Depolama ve Temizlik

1. Her video YouTube'a **başarıyla yüklendikten sonra**, yer kaplamaması için **önceki videoların dosyaları
   komple silinir** (GitHub deposu, GitHub Actions dosyaları ve geçici dosyalar).
2. Silme işlemi yalnızca yüklemenin başarılı olduğu doğrulandıktan sonra yapılır.
3. **YouTube kanalındaki yayınlanmış videolar silinmez.** Silinen şey bizim depolama alanımızdaki
   dosyalardır. (Kanaldan video silmek yalnızca kanal sahibinin açık talimatıyla yapılır.)

## 8. Platform Kuralları (Kanalın Güvenliği İçin)

- Sağlığa zarar verebilecek yanlış bilgi, gerçek ve yaşayan kişiler hakkında karalayıcı iddia verilmez.
- YouTube'un yapay zekâ / gerçekçi sentetik içerik bildirimi gerektiren durumlarda bildirim yapılır.
- Her bölüm özgün olur; birbirinin tekrarı, şablon gibi seri üretilmiş videolar yapılmaz
  (YouTube bu tür içerikte para kazanmayı kısıtlıyor).
