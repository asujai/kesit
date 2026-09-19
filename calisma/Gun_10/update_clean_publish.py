import json

with open("calisma/Gun_10/spec.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

# Update publish texts
spec["publish"]["youtube"]["title_3"] = "Bildirim Yağmuru Zihnimizi Nasıl Yavaşlatıyor? | Johann Hari"

spec["publish"]["instagram"]["caption"] = (
    "'Stolen Focus' (Çalınan Dikkat) kitabının yazarı Johann Hari (@johann.hari), "
    "dikkatimizi ve zihnimizi yavaşlatan tehlikeyi açıklıyor:\n\n"
    "'Hewlett-Packard çalışanları üzerinde yapılan bilimsel bir deneyde iki grup incelendi. "
    "İlk gruba işlerini kesintisiz yapmaları söylendi. İkinci grup ise sürekli e-posta ve mesaj bildirimleriyle bölündü. "
    "Test sonuçları dikkat çekiciydi: Sürekli bölünenlerin IQ seviyesi tam 10 puan düştü!\n\n"
    "10 IQ puanının ne demek olduğunu anlamak için şunu düşünün: Şu an oturup ot içseydiniz zekanız 5 puan düşerdi. "
    "Yani sürekli bildirimlerle bölünmek, uyuşturucunun beyne verdiği zararın tam İKİ KATI!'\n\n"
    "Masada tek bir şeye odaklanmak gelecekteki en büyük süper gücünüzdür."
)

with open("calisma/Gun_10/spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)

print("Updated spec.json with clean non-sensational publication copy.")
