# Gerçek Gizem — Google Cloud Text-to-Speech ile Türkçe Seslendirme Araştırması

> Araştırma tarihi: Kasım 2026. Kaynaklar: Google resmî sayfalarının arama alıntıları ve
> Google'ın resmî API tanımı (googleapis deposu, `cloud_tts.proto`). Resmî dokümana doğrudan erişilemedi.
> ⚠ = ilk canlı API testinde doğrulanacak.

## 1. Türkçe Sesler

| Kademe | Türkçe | Değerlendirme |
|---|---|---|
| Standard / WaveNet | Var (tr-TR-Standard-A…E, tr-TR-Wavenet-A…E) | Eski teknoloji, uzun anlatımda robotik |
| Neural2 / Studio | ⚠ Muhtemelen yok | — |
| **Chirp 3: HD** | **Var, genel kullanımda (GA)** | **Doğal ve uzun anlatımda en güvenilir** |
| Gemini-TTS (2.5 Flash / Pro) | Var ⚠ | En duygulu; ancak Türkçede kelime atlama, robotikleşme ve yanlış okuma ("Emre" → "Emir") raporları var |

Chirp 3 HD ses adları `tr-TR-Chirp3-HD-<Ad>` biçiminde. Derin erkek anlatıcı adayları:
**Charon, Orus, Fenrir, Algenib, Alnilam** (⚠ hepsinin Türkçede olduğu canlı listeyle doğrulanacak).

## 2. Özellikler (Chirp 3 HD)

- **Duraklama:** `markup` alanında `[pause short]`, `[pause]`, `[pause long]` etiketleri.
- **SSML:** Sınırlı; `<break>`, `<prosody>`, `<emphasis>` desteklenmiyor ⚠.
- **Hız:** `speakingRate` 0,25–2,0. **Ses perdesi (pitch) desteklenmiyor olabilir** ⚠.
- **Özel telaffuz:** `custom_pronunciations` (IPA) Türkçede çalışıyor olabilir ⚠; yedek yol: yabancı adları Türkçe okunuşla yazmak.
- **Gemini-TTS:** "alçak, gergin anlat" gibi üslup talimatı alır; ama deterministik değil, aynı metin her seferinde farklı çıkabilir.

## 3. Sınırlar

- Chirp 3 HD: istek başına **5.000 bayt** (Türkçe harfler 2 bayt → pratikte ~4.300 karakter).
- Gemini-TTS: metin ≤4.000 bayt; Pro modelde ~655 sn'yi aşan ses kesilir.
- Kota: Chirp 3 için dakikada 200 istek.
- **Ses formatı:** MP3 yalnızca 32 kbps (düşük kalite) → **LINEAR16 (WAV) 24 kHz** kullanılacak.
- Long Audio Synthesis API, Google Cloud Storage ve servis hesabı gerektiriyor; telefondan kurulum için uygun değil, gerek de yok.

## 4. Fiyat

| Kademe | 1 milyon karakter | Aylık ücretsiz |
|---|---|---|
| Standard | $4 | 4M karakter |
| **Chirp 3 HD** | **$30** | **1M karakter** |
| Neural2 | $16 | 1M |
| Gemini-TTS 2.5 Pro | Token bazlı | **Ücretsiz kota yok** |

- Ücretsiz kotada bile **faturalandırma hesabı zorunlu**. Yeni hesaplara 90 gün geçerli $300 deneme kredisi.
- **Tahmin (ayda 8 bölüm × 30 bin karakter = 240 bin):**
  - **Chirp 3 HD: $0** (1M ücretsiz kotanın içinde; 3 kat yeniden seslendirmede bile).
  - Gemini 2.5 Pro: ayda ~$6 + yeniden denemeler.

## 5. Kimlik Doğrulama

- Telefondan en kolay yol: **kısıtlı API anahtarı** → GitHub Secret `GOOGLE_CLOUD_API_KEY`.
- Anahtar yalnızca Cloud Text-to-Speech API (gerekirse Speech-to-Text) ile kısıtlanır; bütçe uyarısı açılır.
- Anahtar `X-Goog-Api-Key` başlığıyla gönderilir (adres satırına yazılmaz, kayıtlara düşmez).
- ⚠ API anahtarının Chirp 3 HD ve Gemini-TTS'de çalıştığı canlı testle doğrulanacak.

## 6. Kalite Kontrol (sesi yazıya geri çevirme)

- **Google Speech-to-Text v1:** API anahtarıyla çalışır ⚠; tek çağrıda en fazla 60 sn ses → ses ≤55 sn'lik dilimlere bölünür. Ayda 60 dk ücretsiz, sonrası ucuz (~$2–4/ay).
- **v2 `chirp_3`:** Türkçede daha iyi; API anahtarı desteği belirsiz ⚠.
- **Ücretsiz alternatif:** GitHub üzerinde faster-whisper (anahtar gerekmez, yavaş).
- Gemini ile transkripsiyon tek başına güvenilmez (hatalı okumayı fark ettirmeden düzeltebilir).

## 7. Uzun Anlatımda İyi Uygulamalar

- Paragraf sınırından bölünür, cümle ortasında asla; parça başı **≤4.800 bayt**.
- Tüm parçalarda aynı ses, aynı hız, aynı örnekleme hızı (24 kHz).
- **Birleştirme:** parça başı/sonundaki sessizlik kırpılır; paragraf arası ~700–900 ms, bölüm arası ~1,5 sn sessizlik;
  uçlara 5–10 ms yumuşak geçiş (tık sesini önler); tüm işlem WAV üzerinde, sıkıştırma en son;
  ses seviyesi ~−14 LUFS'ye normalize edilir.

## Uygulanacak Kurallar

1. Başlangıç: **Chirp 3 HD, tr-TR**. Charon, Orus, Fenrir, Algenib, Alnilam aynı paragrafla denenir; kanal sahibi seçer.
2. Gemini 2.5 Pro TTS yalnızca karşılaştırma testinde; kalite kontrolü geçmeden üretime alınmaz.
3. Ayarlar: `LINEAR16`, 24 kHz, `speakingRate` 0,90–0,95; pitch kullanılmaz.
4. Girdi `markup` alanıyla; tüm sayılar önceden Türkçe yazıya çevrilmiş; yabancı adlar Türkçe okunuşla (veya IPA telaffuz).
5. Paragraf bazlı parçalar (≤4.800 bayt); birleştirme 7. bölümdeki kurallarla.
6. Kimlik: kısıtlı API anahtarı `GOOGLE_CLOUD_API_KEY`; bütçe uyarısı açık.
7. Kalite kontrol: her parça yazıya çevrilir, metinle kelime kelime karşılaştırılır; fark varsa en fazla 3 kez yeniden seslendirilir; yine hatalıysa iş durur, hatalı ses yüklenmez.
8. Maliyet: Chirp 3 HD ile ayda ~$0; kontrol için ~$2–4.

## Açık Sorular (ilk canlı testte cevaplanacak)

- Kesin Türkçe ses listesi (`voices:list?languageCode=tr-TR`)
- API anahtarı Chirp 3 HD / Gemini-TTS / Speech-to-Text v2'de çalışıyor mu?
- Türkçede `[pause long]` ve `custom_pronunciations` çalışıyor mu?
- Gemini-TTS Türkçede uzun parçalarda kelime atlıyor mu?
- Güncel fiyatlar (konsoldaki fiyat sayfasından)

## Kaynaklar

- https://cloud.google.com/text-to-speech/docs/chirp3-hd
- https://cloud.google.com/text-to-speech/docs/gemini-tts
- https://cloud.google.com/text-to-speech/pricing
- https://cloud.google.com/text-to-speech/quotas
- https://docs.cloud.google.com/text-to-speech/docs/release-notes
- https://github.com/googleapis/googleapis/tree/master/google/cloud/texttospeech/v1
- https://cloud.google.com/speech-to-text/v2/docs/chirp_3-model
- https://cloud.google.com/speech-to-text/pricing
- https://cloud.google.com/free
- https://discuss.ai.google.dev/t/turkish-voice-degrades-to-robotic-tone-in-12-2025-model-and-3-1-preview-has-phonetic-skipping-errors-e-g-emre-emir/142851
- https://discuss.ai.google.dev/t/issues-with-gemini-tts-2-5-pro-in-ai-studio-blank-audio-voice-drift-pacing-changes/133199
