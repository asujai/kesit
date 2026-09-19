import os
import json
from datetime import datetime

# 1. Update Asset Registry
registry_path = "assets/asset_registry.json"
with open(registry_path, "r", encoding="utf-8") as f:
    reg = json.load(f)

assets_data = reg.setdefault("assets", {})

new_assets = [
    {
        "provider": "pexels",
        "asset_id": "6327106",
        "media_type": "video",
        "description": "Friends talking at table holding smartphone",
        "query": "talking friend smartphone table",
        "tags": ["friends", "talking", "smartphone", "table"],
        "cut_id": "c01_talking_holding_phone",
        "start_t": 7.0,
        "end_t": 11.0
    },
    {
        "provider": "pexels",
        "asset_id": "6611951",
        "media_type": "video",
        "description": "Person holding smartphone silent in hand",
        "query": "holding smartphone silent dark",
        "tags": ["holding", "smartphone", "silent", "hand"],
        "cut_id": "c02_silent_phone_hand",
        "start_t": 11.0,
        "end_t": 16.5
    },
    {
        "provider": "pexels",
        "asset_id": "6953394",
        "media_type": "video",
        "description": "Dinner table with friends using phone",
        "query": "friends dinner table smartphone",
        "tags": ["dinner", "table", "friends", "smartphone"],
        "cut_id": "c03_dinner_table_phone",
        "start_t": 27.2,
        "end_t": 32.4
    },
    {
        "provider": "pexels",
        "asset_id": "6374206",
        "media_type": "video",
        "description": "Smartphone lying on wooden table",
        "query": "phone on wooden table",
        "tags": ["phone", "wooden", "table", "facedown"],
        "cut_id": "c04_phone_on_table",
        "start_t": 32.4,
        "end_t": 40.8
    }
]

now_iso = datetime.now().isoformat()
for a in new_assets:
    key = f"pexels_{a['asset_id']}"
    entry = assets_data.setdefault(key, {
        "provider": a["provider"],
        "asset_id": a["asset_id"],
        "media_type": a["media_type"],
        "description": a["description"],
        "query": a["query"],
        "tags": a["tags"],
        "file_hash": "",
        "created_at": now_iso,
        "used_in": [],
        "status": "approved"
    })
    entry["used_in"].append({
        "day": "Gun_7",
        "start_t": a["start_t"],
        "end_t": a["end_t"],
        "duration": round(a["end_t"] - a["start_t"], 2),
        "notes": f"Cut {a['cut_id']}",
        "timestamp": now_iso
    })

with open(registry_path, "w", encoding="utf-8") as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)

print("Asset registry updated successfully.")

# 2. Create Gun_7 spec.json
with open("calisma/Gun_7/subtitles.json", "r", encoding="utf-8") as f:
    subtitles = json.load(f)

spec = {
    "meta": {
        "id": "gun_7_simon_sinek",
        "day": "Gun_7",
        "title": "Telefonu Masaya Koymanın Gizli Psikolojisi | Simon Sinek",
        "topic": "Telefonu Masaya Koymak, Bilinçaltı Mesajlar ve Sosyal Kopuş",
        "speaker": "Simon Sinek",
        "transcript_path": "calisma/Gun_7/sub_sinek.en.vtt",
        "provenance": {
            "source_video": {
                "raw_video_path": "calisma/Gun_7/clean_raw_sinek.mp4",
                "in_point": 0.0,
                "out_point": 44.80,
                "duration": 44.80
            },
            "candidate": {
                "selection_mode": "agent_editorial",
                "in_point": 0.0,
                "out_point": 44.80,
                "duration": 44.80,
                "rationale": "Simon Sinek demonstrates the psychological signal of having a smartphone visible on the table, ending with the viral punchline that putting it upside down is not more polite."
            }
        }
    },
    "source": {
        "raw_video_path": "calisma/Gun_7/clean_raw_sinek.mp4",
        "in_point": 0.0,
        "out_point": 44.80,
        "fps": 25,
        "target_width": 1080,
        "target_height": 1920
    },
    "audio": {
        "bgm_path": "assets/audio/music1_eternity.m4a",
        "voice_gain": 1.0,
        "bgm_gain": 0.23,
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
            "id": "c01_talking_holding_phone",
            "source_file": "calisma/Gun_7/dynamic_brolls/c01_talking_holding_phone.mp4",
            "provider": "pexels",
            "asset_id": "6327106",
            "in_point": 2.0,
            "start_t": 7.0,
            "end_t": 11.0,
            "speed": 1.0
        },
        {
            "id": "c02_silent_phone_hand",
            "source_file": "calisma/Gun_7/dynamic_brolls/c02_silent_phone_hand.mp4",
            "provider": "pexels",
            "asset_id": "6611951",
            "in_point": 1.0,
            "start_t": 11.0,
            "end_t": 16.5,
            "speed": 1.0
        },
        {
            "id": "c03_dinner_table_phone",
            "source_file": "calisma/Gun_7/dynamic_brolls/c03_dinner_table_phone.mp4",
            "provider": "pexels",
            "asset_id": "6953394",
            "in_point": 1.0,
            "start_t": 27.2,
            "end_t": 32.4,
            "speed": 1.0
        },
        {
            "id": "c04_phone_on_table",
            "source_file": "calisma/Gun_7/dynamic_brolls/c04_phone_on_table.mp4",
            "provider": "pexels",
            "asset_id": "6374206",
            "in_point": 1.0,
            "start_t": 32.4,
            "end_t": 40.8,
            "speed": 1.0
        }
    ],
    "subtitles": subtitles,
    "publish": {
        "youtube": {
            "title_1": "Telefonu Masaya Koymak Ne Anlama Geliyor? | Simon Sinek",
            "title_2": "Ters Çevirmek Kibarlık Değil! (Gizli Mesaj)",
            "title_3": "Bilinçaltının Bu Tuzağına Düştün mü? | Simon Sinek Uyarısı",
            "description": "Telefonunuzu masaya koyduğunuzda veya elinizde tuttuğunuzda karşınızdakine aslında ne mesaj veriyorsunuz? Simon Sinek, bir toplantıda veya aile yemeğinde masaya bırakılan telefonun bilinçaltında 'Şu an en önemli şey sen değilsin' hissi yarattığını ve telefonu ters çevirmenin neden kibarlık olmadığını açıklıyor.",
            "tags": [
                "telefonbağımlılığı",
                "simonsinek",
                "dijitaldetoks",
                "psikoloji",
                "iletişim",
                "odaklanma",
                "shorts"
            ],
            "pinned_comment": "Yemekte veya toplantıda telefonu masaya koyar mısınız? Yorumlarda dürüstçe yazın, tartışalım."
        },
        "youtube_en": {
            "title_1": "Putting Your Phone on the Table Sends a Message | Simon Sinek",
            "title_2": "Face Down is NOT More Polite! | Simon Sinek #Shorts",
            "title_3": "The Hidden Psychology of Your Phone on the Table",
            "description": "What does having your phone on the table actually say to people around you? Bestselling author and thinker Simon Sinek reveals the subtle psychological message your phone sends in meetings and family dinners: 'You are not the most important thing to me right now.' And why flipping it face down doesn't make it polite.\n\n#simonsinek #phoneaddiction #psychology #shorts #digitaldetox #relationships",
            "tags": [
                "simon sinek",
                "phone addiction",
                "psychology",
                "relationships",
                "communication",
                "digital detox",
                "shorts"
            ],
            "pinned_comment": "Do you keep your phone on the table during meals? Be honest below! 👇"
        },
        "instagram": {
            "hook": "Telefonunu masaya ters koyunca kibar olduğunu mu sanıyorsun? Simon Sinek'ten tokat gibi gerçek!",
            "caption": "Bir toplantıda, kafede veya ailenizle yemek yerken telefonu masaya koyduğunuzda ne oluyor?\n\nSimon Sinek açıklıyor:\n1. Telefon çalmasa veya titremese bile, elinizde veya masada durması karşınızdakine bilinçaltından şu mesajı verir: \"Şu an benim için en önemli şey sen değilsin.\"\n2. Telefonu ters çevirmek daha kibar bir davranış değildir; masada olduğu sürece dikkat bölücüdür.\n\nGerçek iletişim, karşınızdakine tüm dikkatinizi verebilmektir.",
            "hashtags": "#telefonbağımlılığı #simonsinek #dijitaldetoks #psikoloji #iletişim #ilişkiler #farkındalık #odaklanma #zihinselnetlik #dijitaldenge #kişiselgelişim #motivasyon #derinodak #zihin #keşfet #sağlıklıyaşam #akıllıkullanım #shorts #reels",
            "cta": "Kaydet ve bir sonraki yemekte telefonunu masaya koyan arkadaşına gönder!"
        }
    },
    "cover": {
        "title": "TELEFONU MASAYA KOYMAK",
        "badge": "KENDİNİ TEST ET",
        "punch_line": "ASLINDA NE ANLAMA GELİYOR?"
    }
}

with open("calisma/Gun_7/spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)

print("spec.json created successfully.")
