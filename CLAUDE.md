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

## 1.1 Kanalın Konu Alanı

Kanal sahibinin kararı (23.11.2026): Derin Gizem'in genel konusu şunlardır:
- **Antik gizemler** (açıklanamayan yapılar, antik teknoloji, kayıp eserler)
- **Kayıp medeniyetler**
- **Çözülmemiş olaylar** (kayıplar, esrarengiz ölümler, açıklanamayan vakalar)
- **Uç bilim** (zaman, evren, bilinç, açıklanamayan sinyaller ve deneyler)

**Din ve inanç konuları ana konu yapılmaz** (peygamberler, kutsal kitaplar, ibadetler, dinlerin kökeni vb.).
Antik mitolojiler yalnızca bir antik gizemin tarihsel bağlamı olarak geçebilir; hiçbir inanç hakkında hüküm verilmez.

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
5. **Örnek alınan kanal: "Gerçeği Bul".** Videolarımız, bu YouTube kanalındaki **anlatım biçimi ve mantığı**
   anlaşılarak oluşturulur (açılış, anlatım tonu, hikâye kurgusu, söylenti–gerçek dengesi, merak döngüleri).
   Öğrenilen şey **tarz ve mantıktır**; o kanalın metinleri, başlıkları, kapakları ve içeriği **kopyalanmaz**.
   Analiz notları: `docs/arastirma-gercegi-bul.md`.

## 3. Seslendirme Kuralları (Edge TTS)

1. Tüm seslendirme **Edge TTS** (Microsoft'un ücretsiz sinir ağı sesleri, `edge-tts` kütüphanesi) ile yapılır.
   Kanal sahibinin kararı, 23.11.2026. Gerekçe: Google Cloud 1.500 TL ön ödeme istedi; ücretsiz yol seçildi.
   Önceki araştırmalar (`docs/arastirma-seslendirme.md` ElevenLabs, `docs/arastirma-google-tts.md` Google)
   referans olarak durur; Edge çalışmayı bırakırsa yedek olarak bunlardan biri kanal sahibine önerilir.
2. Edge TTS anahtar gerektirmez. İleride başka bir servis için anahtar gerekirse anahtar **asla** sohbete,
   koda veya depoya yazılmaz; GitHub **Settings → Secrets and variables → Actions** bölümüne eklenir.
3. Edge TTS özel SSML kabul etmez: ton `rate` (hız) ve `pitch` (ses perdesi) ile, duraklamalar
   noktalama ile ve paragraflar arasına bizim eklediğimiz kontrollü sessizlikle sağlanır.
4. Edge TTS'in verdiği kelime zamanlamaları (WordBoundary) ses–görüntü–altyazı eşlemesinde kullanılır.
5. Edge TTS bir gün hata verirse sistem sessizce kötü ses üretmez; durur ve durumu bildirir.
   **Seçilen ses (kanal sahibinin seçimi, ses testi örnek 07):** `tr-TR-AhmetNeural`, hız `-10%`, ses perdesi `-5Hz`.
   Bu ayarlar tüm videolarda ve Shorts'ta sabit kalır; değişiklik yalnızca kanal sahibinin onayıyla yapılır.
6. **Yanlış seslendirme kesinlikle olmamalı.**
   - **Noktalama işaretlerine** kesinlikle dikkat edilir; cümleler doğru yerde durur, doğru vurguyla okunur.
   - **Sayılar kesik kesik okunmamalı.** Yıllar, tarihler, büyük sayılar, yüzdeler, ondalıklar,
     sıra sayıları ve Roma rakamları seslendirmeden önce **Türkçe yazıya çevrilir**
     (ör. `1947` → "bin dokuz yüz kırk yedi", `%40` → "yüzde kırk", `XIV.` → "On Dördüncü").
   - Yabancı özel isimlerin okunuşu kontrol edilir.
7. Üretilen ses **kontrol edilir** (yazıya geri çevrilip metinle karşılaştırılır);
   hatalı bölüm varsa o bölüm yeniden seslendirilir. Hatalı ses yüklenmez.
8. Seslendirme en iyi sonuç için araştırmaya dayalı ayarlarla yapılır. Sayı çevirme, yabancı isim okunuşu,
   parçalara bölme, parçaları birleştirme ve kalite kontrol kuralları `docs/arastirma-seslendirme.md` ve
   `docs/arastirma-google-tts.md` dosyalarından Edge TTS'e uyarlanarak uygulanır.

## 3.1 Ses ve Görüntü Uyumu

Ses ve görüntü **net şekilde oturur** ve birbiriyle **tutarlı** olur:
1. **İçerik uyumu:** Ekranda o an anlatılan şey gösterilir. Anlatıcı bir mekândan, nesneden, tarihten
   veya kişiden bahsediyorsa görüntü de onunla ilgilidir; konuyla alakasız "dolgu" görüntü kullanılmaz.
2. **Zamanlama uyumu:** Görüntü geçişleri cümle ve paragraf sınırlarına denk gelir; bir cümlenin
   ortasında alakasız bir kesme yapılmaz. Görüntü süreleri seslendirmenin gerçek sürelerine göre hesaplanır
   (tahmini süreyle değil).
3. **Altyazı uyumu:** Altyazılar kelime kelime sesle eş zamanlı akar; sesten önce veya sonra görünmez.
   Altyazıda yazılan metin, seslendirmede okunan metinle birebir aynıdır (yabancı isimler orijinal yazımıyla).
4. **Müzik ve ses efekti yok:** Videolarda ve Shorts'ta **müzik ve ses efekti kullanılmaz**; videoda yalnızca
   anlatıcının sesi bulunur (kanal sahibinin kararı, 23.11.2026).
   Tempo ve vurgu; anlatıcının sesi, bilinçli sessizlik anları ve görüntü geçişleriyle sağlanır.
   Videonun tekdüzeleşmemesi için görsel ritim (geçişler, yakınlaştırmalar, ekran yazıları) özellikle canlı tutulur.
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

## 6. Telifsiz Görsel ve Video

1. Kullanılan tüm video ve fotoğraflar **başımıza dert açmayacak şekilde telifsiz** kaynaklardan seçilir
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
