import json

subtitles_tr = [
    {
        "id": "sub_01",
        "start": 0.1,
        "end": 2.0,
        "text": "Hewlett-Packard çalışanlarıyla",
        "highlight": "Hewlett-Packard"
    },
    {
        "id": "sub_02",
        "start": 2.15,
        "end": 4.1,
        "text": "küçük bir deney yaptı.",
        "highlight": "deney yaptı"
    },
    {
        "id": "sub_03",
        "start": 4.25,
        "end": 6.0,
        "text": "Onları iki gruba ayırdılar:",
        "highlight": "iki gruba"
    },
    {
        "id": "sub_04",
        "start": 6.15,
        "end": 9.2,
        "text": "İlk gruba: 'İşinizi yapın,\nkimse sizi bölmeyecek' dendi.",
        "highlight": "bölmeyecek"
    },
    {
        "id": "sub_05",
        "start": 9.35,
        "end": 12.4,
        "text": "Gününüzü kesintisiz tamamlayın.",
        "highlight": "kesintisiz"
    },
    {
        "id": "sub_06",
        "start": 12.55,
        "end": 15.6,
        "text": "İkinci grup ise sürekli e-posta\nve mesajlarla bölündü.",
        "highlight": "mesajlarla bölündü"
    },
    {
        "id": "sub_07",
        "start": 15.75,
        "end": 18.6,
        "text": "Yoğun bir bildirim\nyağmuruna tutuldular.",
        "highlight": "bildirim"
    },
    {
        "id": "sub_08",
        "start": 18.75,
        "end": 21.4,
        "text": "Ve ardından herkesin\nIQ seviyesi test edildi.",
        "highlight": "IQ seviyesi"
    },
    {
        "id": "sub_09",
        "start": 21.55,
        "end": 26.0,
        "text": "Bölünenlerle bölünmeyenler\nkarşılaştırıldığında...",
        "highlight": "karşılaştırıldığında"
    },
    {
        "id": "sub_10",
        "start": 26.15,
        "end": 31.0,
        "text": "Sürekli bölünenlerin IQ'sunun\n10 puan düştüğü görüldü!",
        "highlight": "10 puan düştüğü"
    },
    {
        "id": "sub_11",
        "start": 31.15,
        "end": 34.0,
        "text": "Bölünmeyenlere kıyasla\ntam 10 puan daha düşük!",
        "highlight": "10 puan daha düşük"
    },
    {
        "id": "sub_12",
        "start": 34.15,
        "end": 38.0,
        "text": "Çünkü sürekli odak değiştirmek\nzihni yorup aptallaştırıyor!",
        "highlight": "odak değiştirmek"
    },
    {
        "id": "sub_13",
        "start": 38.15,
        "end": 41.5,
        "text": "Peki 10 IQ puanı düşüş\nne anlama geliyor biliyor musunuz?",
        "highlight": "10 IQ puanı"
    },
    {
        "id": "sub_14",
        "start": 41.65,
        "end": 44.3,
        "text": "Şu an oturup ot veya\nuyuşturucu içseydik...",
        "highlight": "içseydik"
    },
    {
        "id": "sub_15",
        "start": 44.45,
        "end": 47.2,
        "text": "...IQ'muz sadece\n5 puan düşerdi!",
        "highlight": "5 puan düşerdi"
    },
    {
        "id": "sub_16",
        "start": 47.35,
        "end": 51.4,
        "text": "Yani sürekli bölünmek,\not içmenin tam İKİ KATI\nzihinsel hasar veriyor!",
        "highlight": "tam İKİ KATI"
    },
    {
        "id": "sub_17",
        "start": 51.55,
        "end": 55.1,
        "text": "Masanızda tek bir şeye odaklanıp\not içmek bile...",
        "highlight": "odaklanıp"
    },
    {
        "id": "sub_18",
        "start": 55.25,
        "end": 62.8,
        "text": "...ayık olup sürekli bölünmekten\nÇOK DAHA AZ ZARARLI!",
        "highlight": "ÇOK DAHA AZ ZARARLI"
    }
]

subtitles_en = [
    {
        "id": "sub_01",
        "start": 0.1,
        "end": 2.0,
        "text": "Hewlett-Packard did a quite small",
        "highlight": "Hewlett-Packard"
    },
    {
        "id": "sub_02",
        "start": 2.15,
        "end": 4.1,
        "text": "experiment with their workers.",
        "highlight": "experiment"
    },
    {
        "id": "sub_03",
        "start": 4.25,
        "end": 6.0,
        "text": "So they split them into two groups:",
        "highlight": "two groups"
    },
    {
        "id": "sub_04",
        "start": 6.15,
        "end": 9.2,
        "text": "The first group was told:\n'Just do your tasks today,",
        "highlight": "Just do your tasks"
    },
    {
        "id": "sub_05",
        "start": 9.35,
        "end": 12.4,
        "text": "and you're not going to be interrupted.'",
        "highlight": "not interrupted"
    },
    {
        "id": "sub_06",
        "start": 12.55,
        "end": 15.6,
        "text": "And the second group was told:\n'Do your tasks,' and they were",
        "highlight": "second group"
    },
    {
        "id": "sub_07",
        "start": 15.75,
        "end": 18.6,
        "text": "interrupted with a heavy amount\nof emails and texts.",
        "highlight": "emails and texts"
    },
    {
        "id": "sub_08",
        "start": 18.75,
        "end": 21.4,
        "text": "And then they tested their IQ.",
        "highlight": "tested their IQ"
    },
    {
        "id": "sub_09",
        "start": 21.55,
        "end": 26.0,
        "text": "After either being distracted\nor not being distracted...",
        "highlight": "distracted"
    },
    {
        "id": "sub_10",
        "start": 26.15,
        "end": 31.0,
        "text": "The people who had been distracted\ntested 10 IQ points lower!",
        "highlight": "10 IQ points lower"
    },
    {
        "id": "sub_11",
        "start": 31.15,
        "end": 34.0,
        "text": "Than the people who had\nnot been distracted.",
        "highlight": "not been distracted"
    },
    {
        "id": "sub_12",
        "start": 34.15,
        "end": 38.0,
        "text": "Because constantly switching\nmakes you less intelligent!",
        "highlight": "less intelligent"
    },
    {
        "id": "sub_13",
        "start": 38.15,
        "end": 41.5,
        "text": "To give you a sense of what\n10 IQ points means:",
        "highlight": "10 IQ points"
    },
    {
        "id": "sub_14",
        "start": 41.65,
        "end": 44.3,
        "text": "If you and me smoked a spliff\nnow together...",
        "highlight": "smoked a spliff"
    },
    {
        "id": "sub_15",
        "start": 44.45,
        "end": 47.2,
        "text": "...our IQ would drop\nby about 5 points.",
        "highlight": "5 points"
    },
    {
        "id": "sub_16",
        "start": 47.35,
        "end": 51.4,
        "text": "So being heavily interrupted has\nDOUBLE the damage of getting stoned!",
        "highlight": "DOUBLE the damage"
    },
    {
        "id": "sub_17",
        "start": 51.55,
        "end": 55.1,
        "text": "You would be better off sitting\nat your desk smoking a spliff...",
        "highlight": "better off"
    },
    {
        "id": "sub_18",
        "start": 55.25,
        "end": 62.8,
        "text": "...than sitting at your desk sober\nand being interrupted all the time!",
        "highlight": "interrupted all the time"
    }
]

with open("calisma/Gun_10/subtitles.json", "w", encoding="utf-8") as f:
    json.dump(subtitles_tr, f, indent=2, ensure_ascii=False)

with open("calisma/Gun_10/subtitles_en.json", "w", encoding="utf-8") as f:
    json.dump(subtitles_en, f, indent=2, ensure_ascii=False)

print(f"Generated subtitles_tr ({len(subtitles_tr)}) and subtitles_en ({len(subtitles_en)}) successfully!")
