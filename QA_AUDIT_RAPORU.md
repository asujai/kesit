# QA & KREATİF DİREKTÖR DENETİM RAPORU (GÜN 2 — YÜKSEK TEMPOLU MİKRO-KESİT SÜRÜMÜ)

---

## 🎬 GÜN 2 YENİDEN ÜRETİM RAPORU (BUILD: Gun_2_20260918_023025_bcd590e2)

* **İncelenen Varlık:** `calisma/Gun_2/master_gun_2.mp4` -> `youtube/Gun_2/Gun_2_Shorts.mp4` & `instagram/Gun_2/Gun_2_Reels.mp4`
* **Build ID:** `Gun_2_20260918_023025_bcd590e2`
* **SHA-256 Hash:** `bcd590e20a4614682283524d70cc43dffab9e46bd79f596be5c332c37574e052`
* **Format:** 1080x1920 (9:16 Dikey) — 46.88 Saniye (25 fps)
* **A/V Sync:** Delta: 0.000s (Kusursuz eşleşme)
* **Ses Ölçümü (EBU R128):** Integrated: **-14.3 LUFS** (Hedef: -14.0 ±0.5 LUFS), True Peak: **-1.4 dBFS** (Hedef: ≤ -1.0 dBFS)
* **Transkript Sadakati:** PASSED (Tüm YouTube başlıkları, Instagram kancası ve açıklama metinleri alıntı/kapsam nitelik denetiminden geçti; 5.000 iddiası "Telefonla Yakın Olanlar" niteliğiyle sınırlandırıldı)
* **Kalıcı Bellek & Varlık Kaydı:** PASSED (`assets/asset_registry.json` kütüğüne tüm kesitler build kimliği ve dosya hash'iyle işlendi)
* **Staged Dağıtım (Showcase Kilidi):** PASSED (Önce `.staging` klasöründe video, kapak ve metinler doğrulandı; kapak denetimi return kodu ile kilitlendi; ardından atomik swap yapıldı)
* **Kalite Kapısı (Release Gate):** **PASSED (ONAYLANDI & VİTRİNLERE DAĞITILDI)**

---

### 📊 16 Mikro-Kesit Hareket Doğrulama (Anti-Freeze Piksel Varyans Analizi)

> **Kritik Kural:** FFmpeg'de `setpts=PTS-STARTPTS+<start>/TB` ve `-stream_loop -1` uygulanarak tüm B-roll'ların donuk kalması engellendi. Her sahnenin $t_1$ ve $t_2$ kareleri arasındaki ortalama piksel farkı ($\Delta$) ölçülerek hareket doğrulanmıştır ($\Delta \ge 0.20$ eşiği):

| Kesit ID | Zaman Aralığı | Süre | Piksel Varyansı ($\Delta$) | Hareket Durumu |
| :--- | :---: | :---: | :---: | :---: |
| `c01_bed_dark` | 2.00s - 3.70s | 1.7s | **0.7892** | ✅ Akıcı Hareket (Karanlık oda) |
| `c02_bed_screen` | 3.70s - 5.50s | 1.8s | **7.8049** | ✅ Akıcı Hareket (Parlama) |
| `c03_bus_passenger`| 5.50s - 7.10s | 1.6s | **47.9488** | ✅ Çok Yüksek Dinamik Hareket |
| `c04_red_light` | 7.10s - 8.80s | 1.7s | **2.2985** | ✅ Akıcı Hareket (Trafik ışığı) |
| `c05_car_hand` | 8.80s - 10.50s | 1.7s | **36.3400** | ✅ Çok Yüksek Dinamik Hareket |
| `c06_driver_look` | 12.10s - 13.80s| 1.7s | **15.8451** | ✅ Yüksek Hareket (Sürücü) |
| `c07_cafe1` | 13.80s - 15.50s| 1.7s | **19.0490** | ✅ Yüksek Hareket (Kafe) |
| `c08_notif_phone` | 15.50s - 17.00s| 1.5s | **7.2317** | ✅ Akıcı Hareket (Bildirim) |
| `c09_cafe2` | 17.00s - 18.60s| 1.6s | **26.9491** | ✅ Çok Yüksek Dinamik Hareket |
| `c10_night_dark` | 20.10s - 21.80s| 1.7s | **0.7080** | ✅ Akıcı Hareket (Gece oda) |
| `c11_pillow_screen`| 21.80s - 23.50s| 1.7s | **0.8727** | ✅ Akıcı Hareket (Ekran ışığı) |
| `c12_blue_face` | 23.50s - 25.20s| 1.7s | **22.9937** | ✅ Yüksek Hareket (Mavi ışık yüz) |
| `c13_phone_chains`| 33.35s - 35.15s| 1.8s | **6.4038** | ✅ Akıcı Hareket (Metafor) |
| `c14_scroll_fast1`| 35.15s - 36.95s| 1.8s | **8.9281** | ✅ 2X Hızlı Akış Hareketi |
| `c15_scroll_feed` | 36.95s - 38.55s| 1.6s | **14.3308** | ✅ 2X Hızlı Feed Kaydırma |
| `c16_scroll_fast2`| 38.55s - 40.35s| 1.8s | **10.4351** | ✅ 1.5X Hızlı Ekrana Dokunuş |

---

### ⏱️ Düzeltilen Konuşmacı / Anlam Zamanlaması
* **Kritik Editoryal Düzeltme:** Önceki kurguda 32.40s'de konuşmacı kesilip B-roll'a geçiyordu; oysa Beyhan Budak'ın "Tabii ki de akıllı telefonlardan!" ifadesi 30.85s - 33.30s aralığındaydı. Yeni kurguda konuşmacı **25.20s - 33.35s** arasında bölünmeden ekranda tutulmuş, doruk retorik sorusu ve cevabı yüz ifadesinde tamamlandıktan sonra (33.35s) B-roll 13'e geçilmiştir.
* **Kapanış Vuruşu:** 40.35s - 46.88s aralığında konuşmacı kapanış cümlesini (*"Ve bazen farkında bile olmadan hayatımızın en büyük bağımlılıklarından biri!"*) kesintisiz tamamlar ve 0.73s eşzamanlı dip-to-black / ses fade-out ile sonlanır.

---

<details>
<summary><b>Eski Raporlar (Gün 1 & Gün 2 İlk Sürüm)</b></summary>

### Gün 2 İlk Sürüm Raporu
* Tarih: 2026-09-18 01:15
* Genel Skor: 9.4 / 10
* Eksiklik: Sahneler 6-8 saniye kaldığı için kullanıcı temposunu yavaş buldu. 16 mikro-kesit ile revize edildi.

### v5 Sinematik Sürüm Raporu (Gün 1)
* Tarih: 2026-09-17
* Genel Skor: 8.0 / 10 (Onaylandı)
* Detay: Furkan Öztürk - Sosyal Medya Kumarhanesi kesiti, -14.1 LUFS, 4 adet 4K B-roll ile onaylanmıştı.

</details>
