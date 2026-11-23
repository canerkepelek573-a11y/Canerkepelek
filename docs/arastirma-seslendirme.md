# Derin Gizem — ElevenLabs ile Hatasız Türkçe Seslendirme Araştırması

> Araştırma tarihi: 23.11.2026. Kaynaklar: ElevenLabs'in resmî Python SDK'sı (resmî API tanımından üretilir)
> ve resmî doküman / yardım merkezi arama özetleri. ⚠ = canlı dokümandan veya küçük bir API testiyle doğrulanmalı.

## 1. Model Seçimi

| Model | Türkçe | İstek başına karakter | `<break>` | Ses etiketi ([whispers]) | Parçaları birbirine bağlama (stitching) |
|---|---|---|---|---|---|
| `eleven_multilingual_v2` | Var | 10.000 | Var | Yok | Var |
| `eleven_v3` | ⚠ listede açıkça görülmedi | 5.000 | Yok | Var | Yok |
| `eleven_v4` (Eylül 2026) | ⚠ 90+ dil | ⚠ 5.000–10.000 | Yok | Var | ⚠ |
| `eleven_flash_v2_5` / turbo | Var | 40.000 | Var | Yok | Var |

**Karar:** Ana anlatım için **`eleven_multilingual_v2`**. Uzun metinde en kararlı model; parça bağlama ve `<break>` destekliyor.
`eleven_v4` daha duygulu ama ses etiketleri "kesin komut değil, yönlendirme"; sıfır hata hedefi için risk. Ayrı A/B testiyle denenecek.

## 2. Sayılar ve Metin Normalizasyonu

- ElevenLabs'in kendi önerisi: sayıları, tarihleri, sembolleri ve kısaltmaları **metinde açıkça yazıya çevirmek**.
  Türkçe sayıların doğru okunacağına dair hiçbir garanti yok.
- Gönderimde `apply_text_normalization="off"` (gövdenin kökünde; `voice_settings` içinde değil).
- `multilingual_v2`, `language_code` parametresini desteklemiyor; gönderilmez.

**Python `num2words` (lang='tr') kütüphanesi hatalı — düzeltmeden kullanılmaz:**
- Boşluk koymuyor: 1947 → "bindokuzyüzkırkyedi"
- Ondalıkları yanlış çeviriyor: 3.05 → "üç virgül beş" (doğrusu "üç virgül sıfır beş")
- Sıra sayısı eki hatalı: 40 → "40ıncı"

**Sonuç:** Kendi Türkçe sayı çeviricimizi yazacağız (birim testli). Kapsaması gerekenler:

| Metinde | Seslendirmeye giden |
|---|---|
| 1947 | bin dokuz yüz kırk yedi |
| 1947'de | bin dokuz yüz kırk yedide |
| 1990'larda | bin dokuz yüz doksanlarda |
| 10.000 | on bin (nokta binlik ayracıdır) |
| 3,5 / 3,05 | üç virgül beş / üç virgül sıfır beş |
| %40 | yüzde kırk |
| 21. yüzyıl | yirmi birinci yüzyıl |
| XIV. Louis | On Dördüncü Louis |
| M.Ö. 300 | milattan önce üç yüz |

## 3. Telaffuz

- IPA/fonem etiketleri yalnızca **İngilizce** için çalışıyor.
- Türkçe için tek yol: **takma ad (alias) kuralları** → yabancı adları Türkçe okunuşla yazmak:
  "Roswell" → "Rozvel", "Loch Ness" → "Lok Nes".
- Bu çeviri seslendirme metninde yapılır; **altyazı ve başlıkta orijinal yazım korunur**.
- Gerekirse aynı kurallar ElevenLabs telaffuz sözlüğüne de eklenir (istek başına en fazla 3 sözlük).

## 4. Uzun Metinde Tutarlılık

- Metin **600–1.500 karakterlik** parçalara, yalnızca paragraf/cümle sınırından bölünür.
- Parçalar **sırayla** üretilir; her istekte son 3 parçanın `previous_request_ids` değeri gönderilir
  (en fazla 3, en yenisi sonda, 2 saatten eski olmamalı). Böylece ses tonu parçalar arasında kaymaz.
- Bozuk bir parça yeniden üretilirken `next_request_ids` de verilir.
- `enable_logging=false` parça bağlamayı bozar; kullanılmaz. Sabit `seed` verilir.

## 5. Ses Ayarları (belgesel / gizem tonu)

| Ayar | Değer | Not |
|---|---|---|
| stability | 0,55 | Düşükse duygu artar ama tutarsızlaşır; yüksekse monotonlaşır |
| similarity_boost | 0,78 | |
| style | 0–0,1 | Doküman 0 öneriyor; yüksek değer dengesizlik yaratır |
| use_speaker_boost | açık | |
| speed | ~0,95 | 0,7–1,2 arası; uç değerler kaliteyi bozar |

"Gizemli" ton, ayarları zorlayarak değil **doğru ses seçimiyle** sağlanır.

## 6. Noktalama ve Duraklamalar

- **Virgül:** nefes ritmi. **Uzun tire (—):** kısa duraklama.
- **Üç nokta (…):** duraklama + gerilim; yalnızca bilinçli gerilim anlarında.
- **Sahne geçişleri:** `<break time="0.8s"/>` – `<break time="1.5s"/>`, parça başına en fazla 2–3 tane (en fazla 3 sn).
- **Kaçınılacaklar:** %, &, / sembolleri; vb., Dr., M.Ö. gibi kısaltmalar; parantez; tamamı BÜYÜK HARF kelimeler; emoji; arka arkaya noktalama.

## 7. Çıktı Formatı, Limitler, Kota

- Format: Pro planda `pcm_44100` (en iyi montaj kalitesi); Creator planda `mp3_44100_192`; tüm planlarda `mp3_44100_128`.
- Eşzamanlı istek sınırı: Free 2, Starter 3, Creator 5, Pro 10. 429 hatasında bekleyip tekrar denenir.
- **Kota tahmini:** 20 dk ≈ 2.600–3.000 kelime ≈ 20–24 bin karakter; 4 Shorts ≈ 5 bin karakter.
  Yeniden üretim payıyla **video başına ≈ 30–38 bin kredi** (multilingual v2'de 1 karakter = 1 kredi ⚠).
- Ses Kütüphanesi (Voice Library) sesleri API'den yalnızca **ücretli planda** kullanılabiliyor; ticari kullanım hakkı da ücretli planla geliyor.

## 8. Ses Adayları (⚠ doğrulanmadı)

Voice Library'de dil filtresi Türkçe yapılıp seçilen modelle test edilecek:
"Can" (derin, sinematik, gizemli), "Cavit" (belgesel/haber), "Yavuz Demir" (derin anlatım), "Ömer Temizbaş" (derin, sakin).

## 9. Otomatik Kalite Kontrol

1. Her parça ElevenLabs Speech-to-Text (Scribe, `language_code="tr"`) ile yazıya geri çevrilir
   (Türkçe kelime hata oranı ~%3–4; Whisper'dan iyi).
2. Hem senaryo hem transkript normalize edilir (küçük harf, noktalamasız, sayılar yazıyla) ve kelime kelime karşılaştırılır.
3. Saniye başına karakter oranı da kontrol edilir (atlanan kelimeyi yakalamak için).
4. Eşiği aşan parça en fazla 3 kez yeniden üretilir; yine olmazsa rapor edilir, **hatalı ses yüklenmez**.
5. Transkripsiyonda `keyterms` kullanılmaz (hatayı gizleyebilir).

## Uygulanacak Kurallar

1. Model: `eleven_multilingual_v2`; model, ses ve ayarlar tüm parçalarda sabit.
2. Gönderilen metinde rakam, sembol, kısaltma kalmaz; kalırsa sistem hata verip durur.
3. `apply_text_normalization="off"`, `language_code` gönderilmez.
4. Kendi Türkçe sayı çeviricimiz kullanılır (yukarıdaki tablonun tamamını kapsar, birim testli).
5. Yabancı adlar için Türkçe okunuş tablosu tutulur; altyazıda orijinal yazım kalır.
6. 600–1.500 karakterlik parçalar, sırayla, `previous_request_ids` ile bağlanarak üretilir.
7. Ses ayarları: stability 0,55 / similarity 0,78 / style 0–0,1 / speaker_boost açık / speed ~0,95 / sabit seed.
8. Duraklamalar virgül, uzun tire ve sınırlı `<break>` ile; üç nokta yalnızca gerilim anlarında.
9. Her parça yazıya geri çevrilip kontrol edilir; hatalı parça en fazla 3 kez yeniden üretilir.
10. Her video öncesi kalan ElevenLabs kredisi kontrol edilir (video başına ~30–38 bin).

## Açık Sorular (ilk API testinde netleşecek)

- `eleven_v3` / `eleven_v4` Türkçe kalitesi ve limitleri
- Seçilecek sesin ID'si
- Planın kredi miktarı ve çıktı formatı

## Kaynaklar

- https://elevenlabs.io/docs/models
- https://elevenlabs.io/docs/changelog/2026/9/28
- https://elevenlabs.io/docs/best-practices/prompting/eleven-v3
- https://elevenlabs.io/docs/best-practices/prompting/normalization
- https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/pronunciation-dictionaries
- https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/request-stitching
- https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-can-i-add-pauses
- https://elevenlabs.io/docs/help-center/technical/how-many-text-to-speech-requests-can-i-make-and-can-i-increase-it
- https://github.com/elevenlabs/elevenlabs-python (resmî SDK)
