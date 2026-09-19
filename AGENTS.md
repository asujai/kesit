# AGENTS.md — Video Otomasyon & Kesit Üretim Pipeline'ı

Bu proje, YouTube üzerindeki uzun videolardan konu bazlı viral/önemli kesitleri otomatik bulan, süreyi kırpan, 9:16 dikey formatına dönüştüren, yüksek kaliteli Pexels/Pixabay B-roll videoları ve dikey görseller ekleyen, profesyonel ses mastering'i (-14 LUFS) uygulayan ve YouTube Shorts ile Instagram Reels için günlük yayın paketleri hazırlayan otonom bir video otomasyon pipeline'ıdır.

## Modeller ve Ortak Çalışma Bilinci
* **Antigravity / Claude / Codex:** Ortak çalışma bilinci. Görev reddi yoktur. Uçtan uca araştırma, indirme, kesme, B-roll kurgulama, ses mastering, QA denetimi ve yayın paketleme otonom yönetilir.

---

## ⚡ 1 Saniyede Proje Hafızası & Pre-Flight Kuralı
Oturum başında modelin 10-15 farklı dosyayı (`SON_DURUM.md`, `ISLEM_GECMISI.md`, `PUANLAMA_GECMISI.md`, `AKTIF_BELLEK.md`, eski günlerin klasörleri) tek tek gezmesi, listelemesi ve aramalar yapması YASAKTIR.
Her oturum başında tek bir komut çalıştırılır:
```bash
python -m engine.runner --preflight
```
Bu komut 1 saniye altında (< 600 ms) tüm hafızayı okur, hedef günü tespit eder ve JEV Sistem 1 karar motoruyla dünün eleştirilerine göre günün birincil odağını ve guardrail kurallarını ajanın önüne serer.

## 🎯 JEV 90+ Viralite Kalite Eşiği Kuralı
Viral kesit avı başlatıldığında (`python -m engine.runner --hunt-topic "..."`):
JEV karar motoru 100 üzerinden 90 ve üzeri (`composite_score >= 90.0`) puan alana kadar durmaz; arama sorgusunu ve video havuzunu genişleterek turları sürdürür. 90 altı vasat veya amatör adaylar şampiyon ilan edilemez.

## 📁 Proje Dizin Mimarisi & Çok Dilli Vitrin Hijyen Protokolü

Kök dizinin ve yayın vitrinlerinin temizliğini korumak için 3 katmanlı çok dilli (Mutfak -> Türkçe Vitrini & İngilizce Vitrini) mimari uygulanır:

```
c:\Users\abdul\kesiit\
├── calisma\
│   └── Gun_X\                          # O günün imalat/çalışma alanı (Mutfak)
│       ├── (ham kesitler, indirilen 4K B-roll'lar, görseller)
│       ├── (ses kırpmaları, ara test dosyaları)
│       ├── subtitles.json              # Türkçe altyazı zamanlamaları
│       ├── subtitles_en.json           # İngilizce altyazı zamanlamaları
│       └── spec.json                   # O güne özel bildirimsel derleme ve yayın spesifikasyonu
│
├── turkce\                             # Türkçe Yayın Vitrinleri
│   ├── youtube\
│   │   └── Gun_X\                      # Gun_X_Shorts.mp4 (TR Altyazılı), Kapak (TR), YOUTUBE_POST_BILGILERI.md
│   └── instagram\
│       └── Gun_X\                      # Gun_X_Reels.mp4 (TR Altyazılı), INSTAGRAM_POST_BILGILERI.md
│
├── ingilizce\                          # İngilizce Yayın Vitrinleri (Global)
│   ├── youtube\
│   │   └── Gun_X\                      # Gun_X_Shorts.mp4 (EN Altyazılı), Kapak (EN), YOUTUBE_POST_BILGILERI.md (EN)
│   └── instagram\                      # Gelecek genişlemesi için hazır (Şimdilik İngilizce video üretilmez)
│
├── assets\
│   └── audio\                          # Ortak telifsiz ambient/sinematik fon müzikleri
├── core\                               # Yeniden kullanılabilir API istemcileri (Pexels, Pixabay, GIPHY)
├── engine\                             # Pipeline derleyici, ses, zaman çizelgesi ve kalite motorları
├── skills\                             # Antigravity ve ajan beceri tanımları (viral-clip-pipeline)
├── .agents\skills\                     # Sub-agent ve skill yerel kopyaları
├── archive_v1_v4\                      # Arşivlenmiş eski deneme ve scratch dosyaları
├── .env                                # API anahtarları (Pexels, Pixabay, GIPHY)
├── AGENTS.md                           # Proje anayasası ve mimarisi
├── SON_DURUM.md                        # Canlı proje durumu ve son işlem özeti
├── ISLEM_GECMISI.md                    # Kronolojik işlem günlüğü
└── QA_AUDIT_RAPORU.md                  # Bağımsız video QA denetim raporu
```

### 🧹 Klasör Temizlik & Ayrım Kuralları
* **Kök Dizin Hijyeni:** Kök dizinde geçici `.jpg`, `.wav`, `.mp4` veya test scripti bırakılamaz. Kök dizinde eski `youtube` veya `instagram` klasörleri yer alamaz.
* **Mutfak İzolasyonu:** B-roll indirmeleri, kesit denemeleri, ses miksajları ve Python derleyicileri SADECE `calisma/Gun_X/` klasöründe yer alır.
* **Vitrin Saflığı:** 
  * `turkce/youtube/Gun_X/` ve `turkce/instagram/Gun_X/` klasörlerinde **asla** ham kesit, B-roll veya script bulunmaz; YouTube vitrini yalnızca nihai yayını (`Gun_X_Shorts.mp4`), dikey kapak görselini (`Gun_X_Shorts_Kapak.jpg`) ve post dokümanını (`.md`) barındırır. Instagram vitrini ise video ve post dokümanını barındırır.
  * `ingilizce/youtube/Gun_X/` vitrini yalnızca İngilizce gömülü altyazılı nihai yayını (`Gun_X_Shorts.mp4`), İngilizce dikey kapak görselini (`Gun_X_Shorts_Kapak.jpg`) ve İngilizce post dokümanını (`YOUTUBE_POST_BILGILERI.md`) barındırır. İngilizce tarafında Instagram videosu üretilmez.

---

## 🎬 Medya ve Kurgu Standartları

1. **Sinematik Video B-Roll Önceliği:** Metafor ve anlatılan olgular Pexels ve Pixabay API'lerinden çekilen gerçekçi dikey 4K/HD video B-roll'lar ile desteklenir.
2. **Fotoğraf & İnfografik Kuralı:** Konunun doğası gerektirdiğinde (istatistik, belge, özel ürün, şema) yüksek çözünürlüklü dikey fotoğraflar ve infografikler ihmal edilmeden estetik biçimde entegre edilir.
3. **Yasak Unsurlar:**
   * Konuşmacının üstüne binen yapay beyaz web bildirim kartları / rozetler KESİNLİKLE YASAKTIR.
   * Kalitesiz, tekrarlanan statik görseller ve çocuksu/amatör GIF çıkartmaları eklenmez.
   * Tekrarlanan yapay 3D CGI animasyonları (sarı/altın renkli nöron/küre modelleri vb.) ve amatör GIF hissiyatı veren yapay stoklar KESİNLİKLE YASAKTIR. Metaforlar daima gerçek insan, gerçek ortam ve sinematik 4K/HD video B-roll'lar ile kurulur.
4. **Anlatı & Otorite Dengesi:** `%45-%50 Konuşmacı` / `%50-%55 Görsel B-Roll` dengesi korunur. Giriş kancası ve kapanış vuruşu ("punchline") konuşmacıda bırakılır.
5. **Ses Mastering:** EBU R128 standardında `-14.0 LUFS` (±0.5) entegre ses ve `≤ -1.0 dBFS` True Peak.
6. **Konuşmacı Çeşitliliği & Ardışık Tekrar Yasağı (Speaker Diversity):**
   * Üst üste aynı konuşmacının videoları KESİNLİKLE ÜRETİLEMEZ (Maksimum 1 ardışık video).
   * Bir konuşmacı kullanıldıktan sonra en az 3 gün / 3 video boyunca o konuşmacı tekrar seçilemez (`cooldown = 3 gün`).
   * YouTube kanalının tek bir kişinin hayran sayfası/tek sesli kanal gibi görünmesini engellemek için içerik havuzu mutlaka farklı uzmanlar arasında dengeli dağıtılmalıdır (örneğin Dr. Jonathan Haidt, Johann Hari, Andrew Huberman, Barış Özcan, Doğan Cüceloğlu, Sinan Canan, James Clear, Ali Abdaal, Haluk Tatar vb.).

---

## 🛠️ Araçlar & Bağımlılıklar
* `Python 3.13`
* `ffmpeg` (loudnorm, amix, overlay, scale, crop, setpts)
* `yt-dlp` (video ve transkript indirme)
* `Pexels API` (Dikey 4K/HD B-roll video motoru)
* `Pixabay API` (Stok video ve yüksek çözünürlüklü görsel motoru)
* `GIPHY API` (Animasyon ve çıkartma motoru)
