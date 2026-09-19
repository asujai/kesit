from engine.subtitle_engine import SubtitleEngine

subtitles = [
    {"id": "sub_01", "start": 0.20, "end": 2.80, "text": "Akıllı telefon, dopamin için", "highlight": "Akıllı telefon"},
    {"id": "sub_02", "start": 2.95, "end": 5.95, "text": "oldukça ilginç bir araçtır.", "highlight": "ilginç bir araçtır"},
    {"id": "sub_03", "start": 6.15, "end": 8.40, "text": "Bugünlerde insanların sürekli", "highlight": "Bugünlerde"},
    {"id": "sub_04", "start": 8.55, "end": 10.80, "text": "mesajlaştığını ve selfie çektiğini", "highlight": "mesajlaştığını"},
    {"id": "sub_05", "start": 10.95, "end": 13.00, "text": "görmek son derece yaygın.", "highlight": "son derece yaygın"},
    {"id": "sub_06", "start": 13.15, "end": 15.00, "text": "Podcast veya müzik dinlemek,", "highlight": "müzik dinlemek"},
    {"id": "sub_07", "start": 15.15, "end": 17.80, "text": "bir işle uğraşırken", "highlight": "bir işle uğraşırken"},
    {"id": "sub_08", "start": 17.95, "end": 19.80, "text": "aynı anda her şeyi yapmak...", "highlight": "aynı anda"},
    {"id": "sub_09", "start": 19.95, "end": 22.20, "text": "Akşam yemeğinde bile", "highlight": "Akşam yemeğinde"},
    {"id": "sub_10", "start": 22.35, "end": 24.50, "text": "telefona kilitlenip yazışmak...", "highlight": "telefona kilitlenip"},
    {"id": "sub_11", "start": 24.65, "end": 26.80, "text": "Tüm bunlar harika görünür,", "highlight": "harika görünür"},
    {"id": "sub_12", "start": 26.95, "end": 29.80, "text": "hayata renk ve zenginlik katar.", "highlight": "renk ve zenginlik"},
    {"id": "sub_13", "start": 29.95, "end": 32.20, "text": "Fakat mesele sadece", "highlight": "Fakat mesele"},
    {"id": "sub_14", "start": 32.35, "end": 34.50, "text": "dikkatin dağılması değildir;", "highlight": "dikkatin dağılması"},
    {"id": "sub_15", "start": 34.65, "end": 36.80, "text": "bu, dopamini üst üste bindirir!", "highlight": "dopamini üst üste"},
    {"id": "sub_16", "start": 36.95, "end": 38.50, "text": "Ve sonuç olarak...", "highlight": "Ve sonuç olarak"},
    {"id": "sub_17", "start": 38.65, "end": 41.20, "text": "Depresyon ve motivasyon kaybının", "highlight": "motivasyon kaybının"},
    {"id": "sub_18", "start": 41.35, "end": 43.50, "text": "artması hiç de sürpriz değil.", "highlight": "hiç de sürpriz değil"}
]

errs = SubtitleEngine.validate_subtitles(subtitles)
print("Subtitle validation errors:", errs)
if not errs:
    print("ALL SUBTITLES ARE 100% VALID!")
