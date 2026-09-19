import json

with open("calisma/Gun_10/subtitles.json", "r", encoding="utf-8") as f:
    subs_tr = json.load(f)

with open("calisma/Gun_10/subtitles_en.json", "r", encoding="utf-8") as f:
    subs_en = json.load(f)

spec = {
  "meta": {
    "id": "gun_10_johann_hari_stolen_focus",
    "day": "Gun_10",
    "title": "Telefon Bildirimleri Zekanızı Nasıl Düşürüyor? | Johann Hari",
    "topic": "Sürekli Bölünme, Bildirim Bağımlılığı, IQ Düşüşü ve Çalınan Dikkat",
    "speaker": "Johann Hari",
    "transcript_path": "calisma/Gun_10/transcript.txt",
    "subtitles_en": subs_en,
    "provenance": {
      "source_video": {
        "raw_video_path": "calisma/Gun_10/base_source.mp4",
        "in_point": 3.10,
        "out_point": 66.15,
        "duration": 63.05
      },
      "candidate": {
        "selection_mode": "agent_editorial",
        "in_point": 3.10,
        "out_point": 66.15,
        "duration": 63.05,
        "rationale": "Johann Hari explains the Hewlett-Packard distraction experiment on The Diary Of A CEO, proving that phone interruptions drop IQ by 10 points—double the cognitive damage of smoking weed."
      }
    }
  },
  "source": {
    "raw_video_path": "calisma/Gun_10/base_source.mp4",
    "crop_filter": "crop=608:1080:656:0,scale=1080:1920",
    "in_point": 3.10,
    "out_point": 66.15,
    "fps": 25,
    "target_width": 1080,
    "target_height": 1920
  },
  "audio": {
    "bgm_path": "assets/audio/music1_eternity.m4a",
    "voice_gain": 1.0,
    "bgm_gain": 0.18,
    "target_lufs": -14.0,
    "fade_out_duration": 0.73
  },
  "watermark": {
    "enabled": True,
    "image_path": "assets/branding/watermark_zen_circle.png",
    "x": "W-w-40",
    "y": "H-h-130"
  },
  "cuts": [
    {
      "id": "c01_corporate_office_workers",
      "source_file": "calisma/Gun_10/dynamic_brolls/c01_corporate_office_workers.mp4",
      "provider": "pexels",
      "asset_id": "8347701",
      "in_point": 1.0,
      "start_t": 4.5,
      "end_t": 8.5,
      "speed": 1.0
    },
    {
      "id": "c02_smartphone_distracted_worker",
      "source_file": "calisma/Gun_10/dynamic_brolls/c02_smartphone_distracted_worker.mp4",
      "provider": "pexels",
      "asset_id": "31485697",
      "in_point": 1.0,
      "start_t": 13.5,
      "end_t": 18.5,
      "speed": 1.0
    },
    {
      "id": "c03_brain_intelligence_scan",
      "source_file": "calisma/Gun_10/dynamic_brolls/c03_brain_intelligence_scan.mp4",
      "provider": "pexels",
      "asset_id": "35003022",
      "in_point": 1.0,
      "start_t": 23.5,
      "end_t": 28.5,
      "speed": 1.0
    },
    {
      "id": "c04_stressed_headache_overwhelmed",
      "source_file": "calisma/Gun_10/dynamic_brolls/c04_stressed_headache_overwhelmed.mp4",
      "provider": "pexels",
      "asset_id": "9080632",
      "in_point": 1.5,
      "start_t": 28.5,
      "end_t": 34.0,
      "speed": 1.0
    },
    {
      "id": "c05_smoke_rising_cinematic",
      "source_file": "calisma/Gun_10/dynamic_brolls/c05_smoke_rising_cinematic.mp4",
      "provider": "pexels",
      "asset_id": "7597753",
      "in_point": 1.0,
      "start_t": 41.5,
      "end_t": 47.0,
      "speed": 1.0
    },
    {
      "id": "c06_social_media_phone_scroll",
      "source_file": "calisma/Gun_10/dynamic_brolls/c06_social_media_phone_scroll.mp4",
      "provider": "pexels",
      "asset_id": "7984179",
      "in_point": 1.0,
      "start_t": 47.0,
      "end_t": 52.5,
      "speed": 1.0
    },
    {
      "id": "c07_deep_work_single_focus",
      "source_file": "calisma/Gun_10/dynamic_brolls/c07_deep_work_single_focus.mp4",
      "provider": "pexels",
      "asset_id": "12894327",
      "in_point": 1.0,
      "start_t": 52.5,
      "end_t": 56.5,
      "speed": 1.0
    }
  ],
  "subtitles": subs_tr,
  "cover": {
    "image_path": "calisma/Gun_10/Gun_10_Shorts_Kapak.jpg",
    "badge": "PODCAST ÖZEL",
    "title_line1": "BİLDİRİMLERİN BÜYÜK ZARARI",
    "title_line2": "IQ SEVİYENİZ 10 PUAN DÜŞÜYOR!"
  },
  "publish": {
    "youtube": {
      "title_1": "Telefon Bildirimleri Zekanızı Nasıl Düşürüyor? | Johann Hari",
      "title_2": "Sürekli Bölünmek IQ'nuzu 10 Puan Düşürüyor! (Şok Bilimsel Deney)",
      "title_3": "Bildirim Yağmuru Zihni Nasıl Felç Ediyor? | Çalınan Dikkat",
      "description": "'Stolen Focus' (Çalınan Dikkat) yazarı Johann Hari, The Diary Of A CEO podcastinde Hewlett-Packard'ın tarihi deneyini anlatıyor: E-posta ve telefon bildirimleriyle sürekli bölünen çalışanların IQ'su tam 10 puan düştü. Bu hasar, uyuşturucunun beyne verdiği zararın tam iki katı!\n\n📌 Kitap: Stolen Focus (Çalınan Dikkat)\n🎙️ Konuşmacı: Johann Hari\n\n#johannhari #stolenfocus #dikkat #odaklanma #shorts #podcast #ekranbağımlılığı #üretkenlik",
      "tags": [
        "johann hari",
        "stolen focus",
        "çalınan dikkat",
        "dikkat eksikliği",
        "bildirim bağımlılığı",
        "ekran bağımlılığı",
        "odaklanma",
        "iq düşüşü",
        "the diary of a ceo",
        "steven bartlett",
        "podcast kesitleri",
        "shorts"
      ],
      "pinned_comment": "Çalışırken telefonunuza gelen bildirimlere anında bakıyor musunuz, yoksa telefonu sessize alıp uzaklaştırabiliyor musunuz? Yorumlarda tartışalım 👇"
    },
    "youtube_en": {
      "title_1": "How Phone Notifications Drop Your IQ by 10 Points | Johann Hari",
      "title_2": "Being Interrupted Has Double the Brain Damage of Getting Stoned!",
      "title_3": "The HP Experiment: Why Constant Switching Makes You Less Intelligent",
      "description": "'Stolen Focus' author Johann Hari explains on The Diary Of A CEO the shocking Hewlett-Packard experiment: workers constantly interrupted by emails and texts saw their IQ drop by 10 points—double the cognitive impact of smoking weed!\n\n📌 Book: Stolen Focus\n🎙️ Speaker: Johann Hari\n\n#johannhari #stolenfocus #attention #focus #shorts #podcast #productivity #screenaddiction",
      "tags": [
        "johann hari",
        "stolen focus",
        "attention span",
        "focus",
        "deep work",
        "screen addiction",
        "the diary of a ceo",
        "steven bartlett",
        "brain rot",
        "shorts"
      ],
      "pinned_comment": "Do you keep your phone notifications on while working, or do you lock it away? Let us know below 👇"
    },
    "instagram": {
      "hook": "Çalışırken gelen bildirimler IQ'nuzu tam 10 puan düşürüyor olabilir.",
      "caption": "'Stolen Focus' (Çalınan Dikkat) kitabının yazarı Johann Hari (@johann.hari), zihnimizi felç eden tehlikeyi açıklıyor:\n\n'Hewlett-Packard çalışanları üzerinde yapılan bilimsel bir deneyde iki grup incelendi. İlk gruba işlerini kesintisiz yapmaları söylendi. İkinci grup ise sürekli e-posta ve mesaj bildirimleriyle bölündü. Test sonuçları şok ediciydi: Sürekli bölünenlerin IQ seviyesi tam 10 puan düştü!\n\n10 IQ puanının ne demek olduğunu anlamak için şunu düşünün: Şu an oturup ot içseydiniz zekanız 5 puan düşerdi. Yani sürekli bildirimlerle bölünmek, uyuşturucunun beyne verdiği zararın tam İKİ KATI!'\n\nMasada tek bir şeye odaklanmak gelecekteki en büyük süper gücünüzdür.",
      "hashtags": "#johannhari #stolenfocus #çalınandikkat #odaklanma #dikkat #ekranbağımlılığı #derinçalışma #üretkenlik #dopamin #psikoloji #kişiselgelişim #farkındalık #zihin #shorts #reels #keşfet #podcast",
      "cta": "Sürekli bildirimlere bakan ve dikkati dağılan bir arkadaşına gönder! 📲"
    }
  }
}

with open("calisma/Gun_10/spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)

print("calisma/Gun_10/spec.json successfully written!")
