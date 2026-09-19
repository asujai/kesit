"""
engine/viral_radar.py — Çoklu Video & Transkript Avcısı (Jev Sistem 1 Radar Motoru)
Codex Entegrasyon Denetimi Madde 31-33 uyarınca:
1. Konu aramasıyla YouTube'dan en az 10 geçerli transkript toplar (yedek aday döngüsüyle).
2. Transkriptleri cümle sınırlarına göre Shorts (28-60s) veya Video Essay (120-300s) pencerelerine ayırır.
3. Jev Sistem 1 karar motoru ile kanca, bağımsızlık, konu uyumu ve viral potansiyeli paralel değerlendirir.
4. Sıralamayı her videonun en iyi kesiti üzerinden yaparak küresel şampiyon kesiti belirler.
5. Kazanan kesitin sadece ilgili zaman aralığını (--download-sections) nokta atışı indirir.
"""

import os
import re
import sys
import json
import time
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

# Proje kökünü sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.jev_client import JevClient, get_openrouter_api_key
from engine.candidate_ranker import CandidateRanker


class ViralRadar:
    """
    Çoklu video kaynaklarını tarayan, transkriptleri Jev ile süzgeçten geçiren
    ve en yüksek etkileşim potansiyelli kesiti seçen otonom radar motoru.
    """

    def __init__(
        self,
        target_valid_transcripts: int = 10,
        max_search_candidates: int = 25,
        mode: str = "shorts", # "shorts" (28-60s) veya "essay" (120-300s)
        max_workers: int = 3,
        temp_dir: Optional[str] = None,
        min_score: float = 90.0,
        max_rounds: int = 5
    ):
        self.target_valid_transcripts = target_valid_transcripts
        self.max_search_candidates = max_search_candidates
        self.mode = mode
        self.max_workers = max_workers
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "kesiit_viral_radar")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.min_score = min_score
        self.max_rounds = max_rounds

        self.jev = JevClient(enable_cache=True)

    # -------------------------------------------------------------
    # 1. YouTube Kaynak Arama ve Transkript Toplama
    # -------------------------------------------------------------

    def search_youtube_videos(self, query: str) -> List[Dict[str, Any]]:
        """
        yt-dlp kullanarak verilen arama sorgusuna en uygun aday videoların
        metadata bilgilerini çeker (video dosyası indirilmez).
        """
        search_target = f"ytsearch{self.max_search_candidates}:{query}"
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--skip-download",
            search_target
        ]

        print(f"[ViralRadar] YouTube üzerinde '{query}' konusu aranıyor (Hedef havuz: {self.max_search_candidates})...")
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            if res.returncode != 0:
                print(f"[ViralRadar] yt-dlp arama uyarısı: {res.stderr[:200]}")
                return []

            candidates = []
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    duration = data.get("duration", 0) or 0
                    # Shorts arıyorsak en az 2 dakikalık, essay arıyorsak en az 8 dakikalık kaynak videoları tercih et
                    min_source_dur = 120 if self.mode == "shorts" else 480
                    if duration >= min_source_dur or duration == 0:
                        candidates.append({
                            "id": data.get("id"),
                            "title": data.get("title", "İsimsiz Video"),
                            "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                            "duration": duration,
                            "uploader": data.get("uploader", "Bilinmeyen"),
                            "view_count": data.get("view_count", 0)
                        })
                except json.JSONDecodeError:
                    continue

            print(f"[ViralRadar] {len(candidates)} adet aday video bulundu.")
            return candidates
        except Exception as e:
            print(f"[ViralRadar] Arama hatası: {e}")
            return []

    def fetch_transcript(self, video_url: str, video_id: str) -> Optional[str]:
        """
        Videonun yalnızca transkriptini/altyazısını (.vtt) indirir.
        Video akışı ASLA indirilmez (--skip-download).
        """
        out_vtt_template = os.path.join(self.temp_dir, f"{video_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "tr,en",
            "--sub-format", "vtt",
            "-o", out_vtt_template,
            video_url
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25, check=True)
            # İndirilen olası altyazı dosyalarını kontrol et
            for lang in ["tr", "en", "tr-orig", "en-orig"]:
                cand_file = os.path.join(self.temp_dir, f"{video_id}.{lang}.vtt")
                if os.path.exists(cand_file) and os.path.getsize(cand_file) > 200:
                    return cand_file

            # Herhangi bir vtt dosyasını tara
            for f in os.listdir(self.temp_dir):
                if f.startswith(video_id) and f.endswith(".vtt"):
                    full_p = os.path.join(self.temp_dir, f)
                    if os.path.getsize(full_p) > 200:
                        return full_p
            return None
        except Exception:
            return None

    def collect_transcripts(self, query: str, exclude_video_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        En az target_valid_transcripts (varsayılan 10) geçerli zaman damgalı transkript
        elde edilene kadar aday videoları sırayla dener.
        """
        candidates = self.search_youtube_videos(query)
        if not candidates:
            return []

        exclude_ids = exclude_video_ids or set()
        valid_pool = []
        print(f"[ViralRadar] Geçerli transkript toplama başladı (Hedef: en az {self.target_valid_transcripts} transkript)...")

        for idx, cand in enumerate(candidates, 1):
            if len(valid_pool) >= self.target_valid_transcripts:
                break

            vid_id = cand["id"]
            if vid_id in exclude_ids:
                continue
            print(f"  [{idx}/{len(candidates)}] Transkript çekiliyor: {cand['title'][:45]}... ({cand['id']})")
            vtt_path = self.fetch_transcript(cand["url"], vid_id)

            if vtt_path:
                try:
                    cues = CandidateRanker.parse_vtt(vtt_path)
                    if len(cues) >= 10:
                        cand["vtt_path"] = vtt_path
                        cand["cue_count"] = len(cues)
                        valid_pool.append(cand)
                        print(f"    -> [BAŞARILI] {len(cues)} konuşma bloğu bulundu. (Toplam geçerli: {len(valid_pool)}/{self.target_valid_transcripts})")
                    else:
                        print(f"    -> [ATLANDI] Altyazı çok kısa ({len(cues)} blok).")
                except Exception as e:
                    print(f"    -> [HATA] Transkript ayrıştırılamadı: {e}")
            else:
                print("    -> [ATLANDI] Altyazı/transkript bulunamadı.")

        if len(valid_pool) < self.target_valid_transcripts:
            print(f"[ViralRadar] UYARI: Hedeflenen {self.target_valid_transcripts} transkript yerine {len(valid_pool)} geçerli transkript toplanabildi.")
        else:
            print(f"[ViralRadar] Tam {len(valid_pool)} adet geçerli transkript başarıyla toplandı!")

        return valid_pool

    # -------------------------------------------------------------
    # 2. Pencerelere Ayırma (Segmentation)
    # -------------------------------------------------------------

    def generate_candidate_windows(self, cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Seçilen moda göre transkripti mantıksal konuşma pencerelerine ayırır:
          - shorts: 28s - 60s
          - essay: 120s - 300s (2 - 5 dakika)
        """
        min_dur = 28.0 if self.mode == "shorts" else 120.0
        max_dur = 60.0 if self.mode == "shorts" else 300.0

        windows = []
        num_cues = len(cues)

        for i in range(num_cues):
            start_t = cues[i]["start"]
            start_text = cues[i]["text"]

            # Anlamsız başlangıç bağlaçlarını ele
            if start_text.lower().startswith(("ve ", "ama ", "fakat ", "çünkü ")) and len(start_text.split()) < 4:
                continue

            for j in range(i + 1, num_cues):
                end_t = cues[j]["end"]
                dur = end_t - start_t

                if dur > max_dur:
                    break

                if dur >= min_dur:
                    window_cues = cues[i:j+1]
                    full_text = " ".join(c["text"] for c in window_cues)
                    windows.append({
                        "start": round(start_t, 2),
                        "end": round(end_t, 2),
                        "duration": round(dur, 2),
                        "hook_text": window_cues[0]["text"],
                        "punchline_text": window_cues[-1]["text"],
                        "full_text": full_text,
                        "cue_count": len(window_cues)
                    })

        # Çok yoğun örtüşen pencereleri seyrelt (Non-Maximum Suppression benzeri)
        filtered = []
        # Her 15 saniyede en fazla 1 pencere alarak çeşitlilik sağla
        last_start = -999.0
        for w in windows:
            if w["start"] - last_start >= 15.0:
                filtered.append(w)
                last_start = w["start"]
                if len(filtered) >= 8: # Video başına en fazla 8 potansiyel pencere değerlendir
                    break

        return filtered

    # -------------------------------------------------------------
    # 3. Jev Sistem 1 Değerlendirmesi
    # -------------------------------------------------------------

    def evaluate_window_with_jev(self, window: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Bir pencereyi Jev modeline gönderir.
        Kanca gücü, bağımsızlık, konu uyumu ve viral potansiyeli hesaplar.
        """
        state = f"Konu: \"{topic}\"\n\nKonuşma Metni:\n\"{window['full_text']}\""

        questions = {
            "is_strong_hook": self.jev.noul(
                instructions="İlk birkaç saniyede izleyiciyi yakalayacak güçlü bir merak, soru veya şok unsuru var mı?",
                true_criteria="Güçlü ve merak uyandıran giriş cümlesi var.",
                false_criteria="Sıradan, bağlamsız veya yavaş giriş."
            ),
            "is_standalone": self.jev.noul(
                instructions="Bu konuşma parçası öncesi ve sonrası olmadan tek başına dinlendiğinde tam ve net bir anlam ifade ediyor mu?",
                true_criteria="Mesajı ve fikri eksiksiz anlaşılıyor.",
                false_criteria="Önceki veya sonraki konuşmalara bağımlı, eksik kalıyor."
            ),
            "topic_relevance": self.jev.score(
                rubric=[
                    "0: Arama konusuyla tamamen alakasız",
                    "1: Dolaylı ve zayıf temas",
                    "2: Konuya değiniyor ama yüzeysel",
                    "3: Konuyla doğrudan ilgili ve faydalı",
                    "4: Konuyu tam kalbinden anlatan mükemmel içgörü"
                ],
                instructions="Metnin aranan konuyla anlamsal derinliği ve odak uyumu"
            ),
            "viral_power": self.jev.score(
                rubric=[
                    "0: Monoton ve sıkıcı",
                    "1: Vasat konuşma",
                    "2: İlginç ama paylaşılmaz",
                    "3: Yüksek izlenme ve etkileşim potansiyeli",
                    "4: Kesinlikle viral, şoke edici veya ufuk açıcı"
                ],
                instructions="Genel sosyal medya viral yayılma gücü (0..4)"
            )
        }

        try:
            res = self.jev.decide(state=state, questions=questions)
            ans = res.get("answers", {})

            hook_prob = ans.get("is_strong_hook", {}).get("noul", 0.5)
            standalone_prob = ans.get("is_standalone", {}).get("noul", 0.5)
            
            raw_topic_score = ans.get("topic_relevance", {}).get("score", 2.0)
            norm_topic_score = ans.get("topic_relevance", {}).get("normalized_1_to_5", raw_topic_score + 1.0)
            
            raw_viral_score = ans.get("viral_power", {}).get("score", 2.0)
            norm_viral_score = ans.get("viral_power", {}).get("normalized_1_to_5", raw_viral_score + 1.0)

            # Ağırlıklı Bileşik Skor (0 - 100 ölçeği)
            composite_score = round(
                (hook_prob * 25.0) +
                (standalone_prob * 25.0) +
                ((norm_topic_score / 5.0) * 25.0) +
                ((norm_viral_score / 5.0) * 25.0),
                2
            )

            evaluated = dict(window)
            evaluated["scores"] = {
                "hook_prob": round(hook_prob, 3),
                "standalone_prob": round(standalone_prob, 3),
                "topic_score": norm_topic_score,
                "viral_score": norm_viral_score,
                "composite_score": composite_score
            }
            evaluated["jev_latency_ms"] = res.get("_latency_ms", 0)
            evaluated["jev_cost_usd"] = res.get("usage", {}).get("cost", 0)
            return evaluated
        except Exception as e:
            print(f"[ViralRadar] Jev puanlama hatası: {e}")
            evaluated = dict(window)
            evaluated["scores"] = {
                "hook_prob": 0.0,
                "standalone_prob": 0.0,
                "topic_score": 0.0,
                "viral_score": 0.0,
                "composite_score": 0.0
            }
            return evaluated

    # -------------------------------------------------------------
    # 4. Orkestrasyon: Tüm Videoları Tara ve Şampiyonu Seç
    # -------------------------------------------------------------

    def hunt_best_clip(
        self,
        topic: str,
        output_manifest_path: Optional[str] = None,
        min_score: Optional[float] = None,
        max_rounds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tam otonom 90+ puan eşikli viral avı:
        1. 90+ puanlık şampiyon bir kesit bulunana kadar arama havuzunu genişletir.
        2. Her turda farklı arama varyasyonları (podcast, TEDx, röportaj, stüdyo) dener.
        3. Pencereleri Jev ile puanlar; composite_score >= min_score (varsayılan 90.0) sağlanınca durur.
        4. Küresel şampiyonu ilan eder ve ayrıntılı manifestoyu kaydeder.
        """
        start_time = time.time()
        target_min_score = float(min_score if min_score is not None else self.min_score)
        max_search_rounds = int(max_rounds if max_rounds is not None else self.max_rounds)

        query_variants = [
            topic,
            f"{topic} podcast",
            f"{topic} TEDx konuşması",
            f"{topic} röportaj söyleşi",
            f"{topic} bilim stüdyo"
        ]

        print(f"\n{'='*70}")
        print(f"🎯 VIRAL RADAR BAŞLATILDI: '{topic}' (Mod: {self.mode.upper()})")
        print(f"🔥 Hedef Kalite Eşiği      : {target_min_score} / 100")
        print(f"🔄 Maksimum Arama Turu     : {max_search_rounds}")
        print(f"{'='*70}")

        seen_video_ids = set()
        video_champions = []
        all_evaluated_clips = []
        rounds_history = []
        champion = None

        for round_idx in range(1, max_search_rounds + 1):
            current_query = query_variants[(round_idx - 1) % len(query_variants)]
            print(f"\n>>> [TUR {round_idx}/{max_search_rounds}] Arama Sorgusu: '{current_query}' <<<")

            transcripts = self.collect_transcripts(current_query, exclude_video_ids=seen_video_ids)
            if not transcripts:
                print(f"[ViralRadar] Tur {round_idx} için yeni transkript bulunamadı. Sonraki sorguya geçiliyor...")
                continue

            for t_data in transcripts:
                seen_video_ids.add(t_data["id"])

            print(f"\n⚡ Jev Sistem 1 Karar Motoru Devreye Giriyor (Tur {round_idx})...")
            round_clips = []

            for v_idx, video_data in enumerate(transcripts, 1):
                vtt_path = video_data["vtt_path"]
                cues = CandidateRanker.parse_vtt(vtt_path)
                windows = self.generate_candidate_windows(cues)

                print(f"  [{v_idx}/{len(transcripts)}] Puanlanıyor: {video_data['title'][:40]} ({len(windows)} pencere)...")

                evaluated_windows = []
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {executor.submit(self.evaluate_window_with_jev, w, topic): w for w in windows}
                    for f in as_completed(futures):
                        res = f.result()
                        res["source_video_id"] = video_data["id"]
                        res["source_video_title"] = video_data["title"]
                        res["source_video_url"] = video_data["url"]
                        res["search_round"] = round_idx
                        evaluated_windows.append(res)
                        all_evaluated_clips.append(res)
                        round_clips.append(res)

                if evaluated_windows:
                    evaluated_windows.sort(key=lambda x: x["scores"]["composite_score"], reverse=True)
                    top_for_video = evaluated_windows[0]
                    video_champions.append(top_for_video)
                    print(f"    -> En iyi kesit skoru: {top_for_video['scores']['composite_score']}/100 "
                          f"({top_for_video['start']}s - {top_for_video['end']}s, {top_for_video['duration']}s)")

            # Mevcut küresel lideri bul
            if video_champions:
                video_champions.sort(key=lambda x: x["scores"]["composite_score"], reverse=True)
                current_leader = video_champions[0]
                current_best_score = current_leader["scores"]["composite_score"]

                rounds_history.append({
                    "round": round_idx,
                    "query": current_query,
                    "transcripts_found": len(transcripts),
                    "clips_evaluated": len(round_clips),
                    "best_round_score": evaluated_windows[0]["scores"]["composite_score"] if evaluated_windows else 0.0,
                    "current_global_best": current_best_score
                })

                # 90+ Eşik Denetimi
                if current_best_score >= target_min_score:
                    print(f"\n🎉 90+ EŞİĞİ SAĞLANDI! ({current_best_score}/100 >= {target_min_score}) - Tur {round_idx}")
                    champion = current_leader
                    break
                else:
                    if round_idx < max_search_rounds:
                        next_q = query_variants[round_idx % len(query_variants)]
                        print(f"\n⚠️ Tur {round_idx} En Yüksek Skoru: {current_best_score}/100 < {target_min_score} eşiği.")
                        print(f"🔄 90+ Kalite Garantisi için Tarama Genişletiliyor (Sonraki: '{next_q}')...")

        if not video_champions:
            raise RuntimeError(f"'{topic}' konusu için hiçbir kesit değerlendirilemedi!")

        video_champions.sort(key=lambda x: x["scores"]["composite_score"], reverse=True)
        champion = champion or video_champions[0]
        meets_threshold = champion["scores"]["composite_score"] >= target_min_score
        total_time = round(time.time() - start_time, 2)

        print(f"\n{'='*70}")
        if meets_threshold:
            print(f"🏆 KÜRESEL 90+ ŞAMPİYON KESİT BULUNDU! (Toplam Süre: {total_time}s)")
        else:
            print(f"⚠️ HEDEF {target_min_score}+ EŞİĞİNE ULAŞILAMADI ANCAK EN İYİ ADAY SEÇİLDİ (Süre: {total_time}s)")
        print(f"{'='*70}")
        print(f"📺 Kaynak Video  : {champion['source_video_title']}")
        print(f"🔗 YouTube URL   : {champion['source_video_url']}")
        print(f"⏱️ Zaman Aralığı : {champion['start']}s -> {champion['end']}s (Süre: {champion['duration']}s)")
        print(f"🔥 Bileşik Skor  : {champion['scores']['composite_score']} / 100")
        print(f"🪝 Kanca Gücü    : %{champion['scores']['hook_prob']*100:.1f}")
        print(f"🧩 Bağımsızlık   : %{champion['scores']['standalone_prob']*100:.1f}")
        print(f"💬 Başlangıç     : \"{champion['hook_text']}\"")
        print(f"💰 Jev Harcaması : ${self.jev.total_cost_usd:.5f} ({self.jev.total_requests} istek, {self.jev.cache_hits} önbellek)")
        print(f"{'='*70}\n")

        manifest = {
            "query": topic,
            "mode": self.mode,
            "target_min_score": target_min_score,
            "meets_quality_threshold": meets_threshold,
            "total_rounds_executed": len(rounds_history),
            "rounds_history": rounds_history,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_unique_videos": len(seen_video_ids),
            "total_evaluated_clips": len(all_evaluated_clips),
            "execution_time_seconds": total_time,
            "jev_stats": {
                "total_requests": self.jev.total_requests,
                "cache_hits": self.jev.cache_hits,
                "total_cost_usd": self.jev.total_cost_usd
            },
            "champion": champion,
            "video_rankings": video_champions
        }

        if output_manifest_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_manifest_path)), exist_ok=True)
            with open(output_manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"[ViralRadar] Ayrıntılı radar manifestosu kaydedildi: {output_manifest_path}")

        return manifest

    # -------------------------------------------------------------
    # 5. Nokta Atışı İndirme
    # -------------------------------------------------------------

    def download_champion_segment(self, champion_data: Dict[str, Any], output_video_path: str) -> str:
        """
        Seçilen şampiyon kesitin SADECE ilgili saniyelerini indirir.
        Böylece GB'larca video indirme yükü sıfıra iner.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        url = champion_data["source_video_url"]
        start_s = champion_data["start"]
        end_s = champion_data["end"]

        # Zaman damgalarını HH:MM:SS formatına çevir
        def sec_to_ts(sec):
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

        section_str = f"*{sec_to_ts(start_s)}-{sec_to_ts(end_s)}"
        print(f"[ViralRadar] Nokta atışı kesit indiriliyor: {section_str} -> {output_video_path}")

        cmd = [
            "yt-dlp",
            "--download-sections", section_str,
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "--force-keyframes-at-cuts",
            "-o", output_video_path,
            url
        ]

        subprocess.run(cmd, check=True)
        print(f"[ViralRadar] Şampiyon video kesiti başarıyla indirildi: {output_video_path}")
        return output_video_path


if __name__ == "__main__":
    radar = ViralRadar(target_valid_transcripts=2, mode="shorts")
    print(f"[ViralRadar] Modül başarıyla yüklendi.")
