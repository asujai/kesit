# Jev entegrasyon denetimi

Tarih: 2026-09-19 01:29 | Model: Codex

## Sonuç
Jev API istemcisi canlı olarak çalışıyor; istenen çoklu video → en iyi kesit → uygun medya → derleme zincirine bağlı değil. Bu çalışma denetimdir; üretim kodu veya nihai videolar değiştirilmedi.

## Doğrulanan mevcut yapı
- Sağlayıcı OpenAI değil: OpenRouter Decisions API üzerinden TypeSafe Jev. İstek modeli `~typesafe/jev-latest`, canlı yanıt modeli `typesafe/jev-1.13-20260917`.
- `core/jev_client.py` içinde noul/choice/score ve iki yardımcı metot var. Tüm Python dosyalarında aramada istemciyi çağıran tek tüketici `tests/test_jev.py`; üretim modüllerinde çağrı yok.
- `engine/runner.py:74-105`: tek `transcript_path`; kesit uygulama yalnızca `--apply-candidate` verilince gerçekleşiyor. Normal çalışmada aday raporu üretmek seçimi uygulamak anlamına gelmiyor (134-139).
- `engine/candidate_ranker.py:131-219`: 28–50 saniye pencereler, Türkçe ağırlıklı kelime/biçim kuralları ve en fazla beş aday. Jev ile anlamsal puanlama veya farklı kaynak videolar arasında karşılaştırma yok. 3–5 dakikalık podcast seçimi bu süre aralığına uymuyor.
- `engine/viral_radar.py` yok; 10 geçerli transkript toplama, eksik transkript yerine başka aday arama, kaynaklar arası sıralama ve kazanandan otomatik video indirme orkestrasyonu yok. Önceki işlem günlüğü de bunu sonraki iş olarak tanımlıyor.
- `core/semantic_selector.py:69-78,135-182`: önceden hazırlanmış queries/subject_action/environment/emotion üzerinden kelime eşleştirme. `spoken_text` yalnızca kayda yazılıyor, puanlamada kullanılmıyor. Aynı adayda spoken_text değiştirilince puanın değişmediği yerel deneyle doğrulandı.
- Video, fotoğraf ve GIF sağlayıcı dalları var; medya türü ve sorgular önceden verilmeli. Pexels sonuç verirse Pixabay aynı sorguda karşılaştırmaya alınmıyor. Bu nedenle tüm kütüphaneler arasından en iyi medya seçimi iddiası da karşılanmıyor.

## Öncelikli bulgular
1. **P1 — Üretim akışı Jev çağırmıyor.** API bağlantı başarısı, otomatik araştırma/seçim entegrasyonu başarısı değildir.
2. **P1 — B-roll uyum değerlendirmesi bağlamsız.** `core/jev_client.py:146-171`: selected_broll ve relevance_score aynı istekte; ortak state yalnızca cümleyi içeriyor. Aday açıklamaları diğer sorunun choice kriterlerinde. TypeSafe her soruyu aynı state üzerinde bağımsız ve izole değerlendirir. Uyum sorusu seçilen sonucu göremez. Önce seçim, sonra seçilmiş aday açıklaması + cümle ile ayrı değerlendirme veya her aday için bağımsız puanlama gerekir.
3. **P2 — Skor ölçeği yanlış sunuluyor.** Beş kriter 0–4 indekslidir; kriter metnine 1–5 yazmak aralığı değiştirmez. `tests/test_jev.py:58,87` ham skoru /5 diye basıyor. 1–5 gösterimi istenirse ham skora 1 eklenmeli; eşikler doğru ölçeğe göre tanımlanmalı.
4. **P2 — Jev testi başarısızlığı güvenilir şekilde bildirmiyor.** `tests/test_jev.py` assert kullanmıyor, hatayı yakalayıp False döndürüyor, __main__ dönüş değerini çıkış koduna aktarmıyor. unittest discovery serbest test fonksiyonunu çalıştırmıyor. Ayrıca anahtar öneki konsola yazdırılıyor; denetimde bu script doğrudan çalıştırılmadı.
5. **P2 — Yanıt doğrulaması ve işletim politikası eksik.** `decide` HTTP 200 JSON'u answers/tip/aralık/choice üyeliği kontrolü yapmadan kabul ediyor. Sahte HTTP 200 boş JSON deneyinde bozuk yanıt kabul edildi. Yeniden deneme, sınırlı paralellik, önbellek, maliyet bütçesi ve düşük güven için karar politikası yok.

## Çalıştırılan kontroller
- `python -m unittest discover -s tests -v`: 13/13 geçti (mevcut pipeline testleri; Jev entegrasyon testi değil). Bazı testler hata/rollback senaryosu amaçlı başarısız kalite kapısı çıktıları veriyor; test sonucu OK. Bir indirme testinde 404 ve retry oluştu.
- Canlı kesit isteği: 848.50 ms; 825 input token; API maliyet alanı $0.000034650. Hook 0.15, standalone 0.89, ham viral score 1.24 (0–4), score confidence 0.53.
- Canlı medya isteği: 575.44 ms; 481 input token; API maliyet alanı $0.000020202. Telefonla dikkati dağılan kişi cümlesi için üç açıklama arasından `phone` seçildi; choice confidence 1.0. Bağlamsız relevance score 2.05 (0–4), confidence 0.10. Seçim örneğinin geçmesi genel kalite garantisi değildir.
- Toplam iki canlı isteğin bildirilen maliyeti $0.000054852. Bu ölçüm uzun transkript, 10 video veya uçtan uca üretim benchmark'ı değildir; 200–300 kat iyileşme kanıtlanmadı.
- Git kontrolü: klasör Git deposu değil; commit üretilemedi. Depo başlatılmadı.

## İstenen akış için somut tamamlama planı
1. Konuyla ilgili kaynakları ara; en az 10 farklı kullanılabilir zaman damgalı transkript elde edilene kadar yedek adayları dene. Yetersiz sonuç varsa gerçek sayıyı açıkça raporla.
2. Transkriptleri cümle sınırlarına göre süre hedeflerine uygun pencerelere ayır; konu uyumu, kanca, bağımsız anlaşılabilirlik ve kapanışı ayrı Jev sorularıyla değerlendir. Video sıralamasını her videonun en iyi kullanılabilir kesiti üzerinden yap; böylece genel olarak iyi fakat kesiti zayıf bir video kazanmaz.
3. Sınırlı eşzamanlı istekler, içerik hash önbelleği, tekrar deneme, token/maliyet sınırı ve açık güven eşikleri ekle. Kaynak URL, transcript, zamanlar ve seçim puanlarını kaydet.
4. Seçilen kesitten sahne ihtiyaçları ve arama sorguları çıkar. Jev serbest metin üretmediği için sorgu üretimini şablonlar veya uygun bir metin üretim modeli yapmalı; Jev önceden oluşturulmuş seçenekleri puanlayabilir.
5. Pexels/Pixabay/GIPHY adaylarını ortak açıklama formatına getir. Gerçek aday metadata'sını ve konuşulan cümleyi aynı state'e koy. Teknik kalite, tekrar kullanımı ve proje GIF kurallarını koruyarak Jev ile puanla; zayıf adayda yeni arama veya konuşmacı görüntüsüne dönüş uygula. Metinden değerlendirme gerçek video karelerini izleme anlamına gelmez; görsel kalite kontrolü ayrıca gerekir.
6. Kazanan kaynak ve kesiti spec/timeline'a bağla. 10 transkriptli uçtan uca test, eksik altyazı, 429/timeout, bozuk yanıt, düşük güven ve alakasız görsel senaryolarını doğrula. Sonrasında gerçek konu üzerinde süre/maliyet/kalite kıyaslaması yap.

## Birincil kaynaklar
- https://docs.typesafe.ai/introduction — sorular bağımsız ve izole değerlendirilir.
- https://docs.typesafe.ai/primitives/score — sıfır tabanlı seviyeler ve confidence.
- https://typesafe.ai/blog/introducing-system-one-models-and-jev — üreticinin hız/verimlilik iddiaları, proje benchmark'ı değildir.

— Codex, 2026-09-19
