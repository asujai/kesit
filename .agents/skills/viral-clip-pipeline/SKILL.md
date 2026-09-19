---
name: viral-clip-pipeline
description: >-
  Uçtan uca otomatik YouTube Shorts ve Instagram Reels video üretim, kesit bulma,
  sinematik B-roll katmanlama, ses mastering, bağımsız QA denetimi ve günlük yayın paketleme becerisi.
---

# Viral Clip Pipeline Becerisi (viral-clip-pipeline)

Bu beceri; uzun YouTube videolarından veya yerel ham kayıtlardan konu bazlı en vurucu kesitleri bulan, 9:16 dikey formata dönüştüren, Pexels ve Pixabay kütüphanelerinden 4K sinematik B-roll'lar ve yüksek kaliteli dikey görseller ekleyen, profesyonel ses mastering'i (-14 LUFS) uygulayan ve YouTube/Instagram için yayın paketlerini günlük klasörler halinde otomatize eden kurumsal standardı tanımlar.

---

## 1. Temel Tasarım Felsefesi ve Katı Kurallar

### 🚫 Anti-Pattern'ler (Asla Yapılmayacaklar)
1. **Yapay Web Bildirim Kartları & Üst Rozetler:** Konuşmacının kafasının üstüne veya kenarına beyaz renkli, gölgeli, yapay web popup kartları koymak kesinlikle YASAKTIR. Video amatör sunum havasına sokulamaz.
2. **Çocuksu Çıkartmalar & Kalp Rozetleri:** Konunun ciddiyetini bozan rastgele gif veya kalp emojisi animasyonları eklenmez.
3. **Statik Görsel Tekrarı:** Düşük çözünürlüklü veya bağlamsız statik fotoğraflar arka arkaya kullanılamaz.

### 💎 Altın Standartlar (Mutlaka Uygulanacaklar)
1. **Sinematik 4K/HD Video B-Roll Önceliği:** Metafor ve anlatılan olaylar Pexels ve Pixabay üzerinden bulunan yüksek kaliteli dikey 4K/HD video b-roll'lar ile görselleştirilir.
2. **Fotoğraf & İnfografik Desteği:** Konunun doğası gerektirdiğinde (örneğin istatistik, özel bir tablo, tarihsel belge veya net bir ürün fotoğrafı) yüksek çözünürlüklü dikey fotoğraflar veya grafikler estetik biçimde kullanılır; görseller ihmal edilmez.
3. **Anlatı & Otorite Dengesi (Altın Oran):**
   - `%45 - %50 Konuşmacı` / `%50 - %55 B-Roll & Görsel` oranı korunur.
   - **Giriş Kancası (00:00 - ~05.0s):** Konuşmacının doğrudan kamerayla göz teması kurduğu, dikkat çeken ilk cümle korunur.
   - **Final Punchline Kancası:** Videonun en can alıcı son cümlesi (örneğin son 10-12 saniye) bölünmeden konuşmacının yüz ifadesine odaklanır.
4. **Temiz Kesim (Vocal Trimming):** Başlangıçta önceki cümlenin yarım hecesi bırakılmaz (en az 50ms nefes payı ile başlar). Bitişte son hece tamamlandıktan sonra 0.5 - 0.8 saniyelik eşzamanlı dip-to-black ve ses fade-out uygulanır.
5. **Ses Mastering (-14.0 LUFS):** EBU R128 standardında entegre ses tam `-14.0 LUFS` (±0.5 LUFS), True Peak `≤ -1.0 dBFS` olmalıdır. Ambient fon müziği 0.12 - 0.15 ses kazancında vokal netliğini bozmadan altta tutulur.

### ⚡ Pre-Flight & JEV Kalite Eşik Kuralları
1. **1 Saniyede Proje Hafızası (Pre-Flight Protokolü):**
   * Oturum başlangıcında 10-15 dosyayı tek tek okumak KESİNLİKLE YASAKTIR.
   * Her oturum tek bir komutla başlatılır: `python -m engine.runner --preflight`
   * Bu komut; son durumu, geçmiş günün puanlarını, eleştirileri ve aktif kısıtları toplayıp JEV Sistem 1 ile günün stratejisini 1 saniyede (< 600 ms) çıkarır.
2. **JEV 90+ Viralite Eşiği:**
   * `python -m engine.runner --hunt-topic "..."` çalıştırıldığında JEV, 100 üzerinden en az 90 puan alan bir kesit bulana kadar (`composite_score >= 90.0`) arama turlarını sürdürür. 90 altı vasat adaylar kabul edilemez.

---

## 2. Günlük Klasörleme ve Yaşam Döngüsü Protokolü

Karmaşayı ve dosya çöpünü engellemek için 3 katmanlı mimari (Mutfak -> Yayın Vitrinleri) uygulanır:

```
c:\Users\abdul\kesiit\
├── engine/                             <-- Ortak Üretim, Zaman Çizelgesi ve QA Motoru
│   ├── spec.py                         <-- Bildirimsel video tanım şeması
│   ├── timeline.py                     <-- FFmpeg zaman çizelgesi derleyicisi (anti-freeze setpts)
│   ├── audio_engine.py                 <-- -14 LUFS mastering ve dinamik ses mikseri
│   ├── subtitle_engine.py              <-- Minimalist Black Pill altyazı rozet motoru
│   ├── quality_gate.py                 <-- Bağımsız QA kalite ve vitrin release kapısı
│   ├── fidelity.py                     <-- Transkript sadakat ve iddia denetleyicisi
│   ├── candidate_ranker.py             <-- Nişe göre en iyi kesit puanlayıcı
│   └── runner.py                       <-- Master CLI arayüzü (`python -m engine.runner`)
│
├── calisma\
│   └── Gun_X\                          <-- O günün imalat/çalışma alanı (Mutfak)
│       ├── spec.json                   <-- O güne özel BİLDİRİMSEL kurgu tanımı (kod yazılmaz)
│       ├── (ham kesitler, indirilen 4K B-roll'lar, ara testler)
│       └── QA_REPORT_*.json            <-- SHA-256 imzalı teknik QA denetim raporu
│
├── youtube\
│   └── Gun_X\                          <-- O günün YouTube Shorts yayın vitrini (SADECE nihai paket)
│       ├── Gun_X_Shorts.mp4            <-- SADECE QA kapısından geçmiş dikey video
│       ├── Gun_X_Shorts_Kapak.jpg      <-- 9:16 sinematik küçük resim (Thumbnail)
│       └── YOUTUBE_POST_BILGILERI.md   <-- Başlık, SEO açıklama, etiketler, sabit yorum
│
├── instagram\
│   └── Gun_X\                          <-- O günün Instagram Reels yayın vitrini (SADECE nihai paket)
│       ├── Gun_X_Reels.mp4             <-- SADECE QA kapısından geçmiş dikey video
│       └── INSTAGRAM_POST_BILGILERI.md <-- Kanca metni, caption, 30 niche hashtag, CTA
│
├── assets\
│   ├── asset_registry.json             <-- Kullanılan tüm stok asset'lerin kalıcı hafızası
│   └── audio\                          <-- Ortak lisanslı fon müzikleri
├── core\                               <-- Modüler ve dayanıklı API istemcileri (retry + timeout)
└── config\                             <-- Niş profili ve editoryal kurallar
```

* **Katı İlke (Release Gate):** `youtube/Gun_X` ve `instagram/Gun_X` vitrinleri `QualityGate` onayı olmadan ASLA güncellenemez. Başarısız veya doğrulanmamış render vitrine kopyalanmaz.

---

## 3. Adım Adım Pipeline İşlem Akışı

### Adım 1: Transkript Analizi & Aday Sıralaması
- `CandidateRanker` ile VTT/Whisper transkriptindeki 30-50s kesitler (kanca gücü, bağlam bütünlüğü, kapanış vuruşu) puanlanır.
- Seçilen ve elenen adaylar `candidate_evaluation.json` dosyasına gerekçeleriyle kaydedilir.

### Adım 2: Çoklu Medya Arama & Anlamsal Seçim
- Körlemesine ilk sonuç (`results[0]`) seçilmez; `VisualNeed` ihtiyaç kartı tanımlanır.
- `AssetRegistry` taranarak son günlerde kullanılan asset'ler elenir (tekrar engelleme).
- İndirmeler atomik yapılır (`.tmp` -> stream/size kontrolü -> asıl dosya adı).

### Adım 3: FFmpeg Kompozisyon ve Anti-Freeze Standartları
FFmpeg filtresinde zamanlama kaymalarını ve donmaları önlemek için şu kurallar ZORUNLUDUR:
1. Her B-roll girişine `-stream_loop -1` eklenmelidir.
2. Her video B-roll dalında mutlaka **`setpts=PTS-STARTPTS+<BaslangicZamani>/TB`** kullanılmalıdır.
3. Hızlandırma varsa önce `setpts=(1/speed)*PTS`, ardından zaman ötelemesi uygulanır.
4. Ölçekleme formatı:
   - Taban video: `[0:v]crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,scale=1080:1920,fps=25[v_base]`
   - Dikey B-roll: `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25`
5. Geçişler: `overlay=enable='between(t,Baslangic,Bitis)':eof_action=pass`
6. Kararma: `fade=t=out:st=CikisBaslangici:d=0.73`
7. Ses Miksajı & Normalizasyon: EBU R128 standardında -14.0 LUFS.

### Adım 4: Bağımsız Kalite ve Release Kapısı (`QualityGate`)
- Her B-roll aralığından iki kare çıkartılarak piksel varyans testi ($\Delta \ge 0.20$) yapılır; donma varsa üretim iptal edilir.
- EBU R128 loudness ve True Peak doğrulanır.
- Altyazı ve paylaşım metinlerinin transkripte sadakati (`SemanticFidelityChecker`) denetlenir.
- Yalnızca tüm kontrolleri geçen üretim vitrinlere kopyalanır.

### Adım 5: Yayın Paketleme (YouTube & Instagram)
Nihai video onaylandığında vitrin dosyaları ve dikey kapak görseli eksiksiz teslim edilir.
1. `youtube/Gun_X/`:
   - `Gun_X_Shorts.mp4`: Nihai render edilmiş altyazılı dikey video.
   - `Gun_X_Shorts_Kapak.jpg`: 9:16 (1080x1920) dikey, yüksek tıklama (CTR) odaklı, AI slop olmayan sinematik küçük resim (thumbnail). Üst %15-%25 güvenli alana 2-3 kelimelik merak uyandırıcı kanca metni yerleştirilir; alt %20 YouTube arayüzü için temiz bırakılır.
   - `YOUTUBE_POST_BILGILERI.md`: 3 alternatif CTR başlık, SEO açıklaması, etiketler ve sabit yorum stratejisi.
2. `instagram/Gun_X/`:
   - `Gun_X_Reels.mp4`: Nihai render edilmiş altyazılı dikey video.
   - `INSTAGRAM_POST_BILGILERI.md`: İlk 2 satırlık kanca, CTA, 25-30 niş hashtag, önerilen kapak karesi zaman kodu.
   - "Daha fazlası" butonuna basılmadan önceki ilk 2 satırlık kanca.
   - Kaydetmeye/Paylaşmaya teşvik eden CTA metni.
   - 25-30 adet niş Türkçe hashtag.
   - Önerilen Reels kapak zaman kodu.

---

## 5. Minimalist Black Pill Altyazı Motoru

Tüm Shorts ve Reels videolarına aşağıdaki standartlarda profesyonel altyazı eklenir:

### 🎨 Görsel Tasarım Standardı

| Parametre | Değer | Açıklama |
| :--- | :--- | :--- |
| **Kapsül Tipi** | Minimalist Black Pill (Birleşik Rozet) | Tek veya çift satırlık metin bloğu tek bir kapsül içinde |
| **Kapsül Rengi** | `#0C0C0E` (RGB 12, 12, 14) | Antrasit siyah |
| **Kapsül Opaklığı** | Alpha: 238 (~%93) | Hem koyu hem açık sahnelerde zemin ayrımı sağlar |
| **Köşe Yuvarlama** | `radius = 24px` | Yumuşak modern hap rozet hissi |
| **İç Boşluk (Padding)** | `pad_x = 32px`, `pad_y = 18px` | Harflerin kapsül kenarına sıkışmaması |
| **Font** | `Segoe UI Bold` (44px) | Yüksek çözünürlükte net, okunabilir sans-serif |
| **Metin Rengi** | `#FFFFFF` (saf beyaz) | Maksimum kontrast |
| **Metin Kasası** | Cümle düzeni (Sentence case) | Doğal konuşma düzeni; tümü büyük harf YASAK |
| **Dikey Konum** | `center_y = 1450px` (1080x1920 canvas) | Konuşmacının çenesinin altı; YouTube/Instagram alt butonlarının üstü |
| **Satır Aralığı** | `line_height = 64px` (çift satırda) | Satırlar arası temiz boşluk |

### 📝 Semantik Bölümleme Kuralları
1. Her altyazı bloğu **2-5 kelimelik anlamsal öbekler** içerir.
2. Maksimum **2 satır** per blok; 3+ satır kesinlikle YASAK.
3. Blok geçişleri konuşmacının nefes aralıklarına ve doğal duraklamalarına senkronize edilir (`silencedetect` ile ölçülür).
4. Bloklar arası minimum **0.15s** sessizlik boşluğu bırakılır (üst üste binme YASAK).

### 🛠️ Teknik Uygulama Akışı
1. Konuşmacının sesinden `speech_recognition` ve `ffmpeg silencedetect` ile milisaniye hassasiyetinde zaman damgaları çıkartılır.
2. Zaman damgaları `calisma/Gun_X/subtitles.json` dosyasına `[[start, end, "metin"], ...]` formatında kaydedilir (UTF-8, Türkçe karakter güvenli).
3. Pillow `ImageDraw.rounded_rectangle` + `anchor='mm'` ile her blok için 1080x1920 boyutunda şeffaf PNG kapsül rozeti üretilir (`sub_badges/sub_XX.png`).
4. FFmpeg `overlay=0:0:enable='between(t,start,end)'` zinciriyle 16+ kapsül nihai videonun üstüne basılır.

### ⚠️ Türkçe Karakter Güvenlik Protokolü
- Altyazı metinleri **ASLA** Python script içine doğrudan hard-coded yazılmaz; her zaman `subtitles.json` dosyasından `json.load(f)` ile okunur.
- JSON dosyası `ensure_ascii=False` ile kaydedilir ve `encoding='utf-8'` ile okunur.
- Render öncesi `ğ` (`U+011F`), `ş` (`U+015F`), `ı` (`U+0131`), `ç` (`U+00E7`), `ö` (`U+00F6`), `ü` (`U+00FC`) karakter kodları doğrulanır.

---

## 4. API İstemcileri Başvuru Kılavuzu

* `core/pexels_client.py`: `search_broll_video(query, orientation='portrait', per_page=5)` ve `search_broll_photo(query, orientation='portrait', per_page=5)`
* `core/pixabay_client.py`: `search_pixabay_videos(query, per_page=5)` ve `search_pixabay_images(query, per_page=5)`
* `core/giphy_client.py`: `search_stickers(query, limit=5)`
* `.env`: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `GIPHY_API_KEY` değişkenlerini içerir.

---

## 7. Günlük Video Puanlama & Sürekli İyileştirme Protokolü

Her günün nihai videosu üretilip yayın vitrinlerine yerleştirildikten sonra, kullanıcıya **6 kategorili bir puanlama anketi** sunulur. Bu puanlar `PUANLAMA_GECMISI.md` dosyasına kalıcı olarak kaydedilir ve pipeline'ın zaman içinde sistematik olarak geliştirilmesine rehberlik eder.

### 📊 Puanlama Kategorileri (1-10)

| # | Kategori | Neyi Ölçer |
| :--- | :--- | :--- |
| 1 | **Kesit Seçimi & Kesim Doğruluğu** | Başlangıç/bitiş noktaları, yarım kelime, akış doğallığı |
| 2 | **Altyazı Kalitesi** | Okunabilirlik, zamanlama senkronu, tasarım profesyonelliği |
| 3 | **Eklenen B-Roll Videoları** | Konuyla uyum, görsel kalite, zamanlama |
| 4 | **Eklenen Fotoğraflar & Görseller** | Gereken yerlerde varlık, kalite, konu bütünlüğüne katkı |
| 5 | **Ses & Müzik Dengesi** | Konuşmacı netliği, fon müziği seviyesi, genel ses dengesi |
| 6 | **Genel Etki & İzlenebilirlik** | Baştan sona izleme isteği, dikkat tutma gücü |

### 🔄 İş Akışı
1. Video tamamlandığında `ask_question` aracıyla kullanıcıya 6 kategorili anket sunulur.
2. Kullanıcının puanları ve serbest yorumları `PUANLAMA_GECMISI.md` dosyasına o günün tablosuna yazılır.
3. Önceki günlerin puanları düşük kalan kategoriler bir sonraki günün üretiminde öncelikli iyileştirme hedefi olarak ele alınır.
4. Ortalama puan trendi takip edilerek pipeline'ın gelişim eğrisi izlenir.


