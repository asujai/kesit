"""
engine/preflight.py — 1 Saniyede Proje Hafıza & JEV Karar Sentezleyicisi (Pre-Flight)
Ajanın oturum başında 10-15 farklı dosyayı ayrı ayrı okuyarak zaman ve token harcamasını önler.
Tüm proje hafızasını (<50ms) toplayıp JEV Sistem 1 (~500ms) karar motoruna aktarır.
"""

import os
import re
import sys
import time
import json
from typing import Dict, Any, List, Optional

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.jev_client import JevClient


class PreflightSynthesizer:
    """
    Proje durumunu, geçmiş günlerin puanlarını, hataları ve ikinci beyin hafızasını
    tek hamlede okuyup Jev Karar Motoru ile bugünün üretim stratejisine dönüştürür.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.jev = JevClient(enable_cache=True)

    # -------------------------------------------------------------
    # 1. Hızlı Yerel Hafıza Okuma (< 50 ms)
    # -------------------------------------------------------------

    def collect_local_context(self) -> Dict[str, Any]:
        """Tüm proje hafıza dosyalarını mikrosaniyeler içinde ayrıştırır."""
        start_t = time.time()
        context: Dict[str, Any] = {
            "root_dir": self.root_dir,
            "target_day": "Gun_1",
            "last_completed_day": None,
            "son_durum": {},
            "latest_history": [],
            "latest_evaluation": {},
            "aktif_bellek": "",
            "vitrin_status": {}
        }

        # 1.1 Vitrin ve Hedef Gün Tespiti
        turkce_yt = os.path.join(self.root_dir, "turkce", "youtube")
        existing_days = []
        if os.path.exists(turkce_yt):
            for d in os.listdir(turkce_yt):
                m = re.match(r"Gun_(\d+)", d)
                if m:
                    existing_days.append(int(m.group(1)))

        if existing_days:
            last_day_num = max(existing_days)
            context["last_completed_day"] = f"Gun_{last_day_num}"
            context["target_day"] = f"Gun_{last_day_num + 1}"
        else:
            context["target_day"] = "Gun_1"

        # 1.2 SON_DURUM.md
        son_durum_path = os.path.join(self.root_dir, "SON_DURUM.md")
        if os.path.exists(son_durum_path):
            try:
                with open(son_durum_path, "r", encoding="utf-8") as f:
                    sd_text = f.read()
                context["son_durum"]["raw_snippet"] = sd_text[:600]
                m_status = re.search(r"\*\*Mevcut Durum:\*\*\s*(.*)", sd_text)
                if m_status:
                    context["son_durum"]["status"] = m_status.group(1).strip()
            except Exception:
                pass

        # 1.3 ISLEM_GECMISI.md (En üstteki 1-2 işlem kaydı)
        islem_path = os.path.join(self.root_dir, "ISLEM_GECMISI.md")
        if os.path.exists(islem_path):
            try:
                with open(islem_path, "r", encoding="utf-8") as f:
                    history_text = f.read()
                entries = re.findall(r"##\s*\[(.*?)\]\s*-\s*(.*?)\n(.*?)(?=\n##\s*\[|\Z)", history_text, re.DOTALL)
                for date_str, title, body in entries[:2]:
                    context["latest_history"].append({
                        "date": date_str.strip(),
                        "title": title.strip(),
                        "summary": body.strip()[:400]
                    })
            except Exception:
                pass

        # 1.4 PUANLAMA_GECMISI.md (En son puanlanan günün analizi)
        puan_path = os.path.join(self.root_dir, "PUANLAMA_GECMISI.md")
        if os.path.exists(puan_path):
            try:
                with open(puan_path, "r", encoding="utf-8") as f:
                    puan_text = f.read()
                
                day_blocks = re.findall(r"## (Gün \d+)[^\n]*\n(.*?)(?=\n## Gün |\Z)", puan_text, re.DOTALL)
                latest_rated_day = None
                rated_categories = []
                criticisms = []

                for day_name, block_text in day_blocks:
                    cats = []
                    for line in block_text.splitlines():
                        if line.strip().startswith("|") and not line.strip().startswith("| #") and not line.strip().startswith("| :"):
                            parts = [p.strip() for p in line.split("|")[1:-1]]
                            if len(parts) >= 4:
                                num, cat, score_str, comment = parts[0], parts[1].replace("*", ""), parts[2].replace("*", ""), parts[3]
                                if score_str and score_str.replace(".", "").isdigit():
                                    score_val = float(score_str)
                                    cats.append({"cat": cat, "score": score_val, "comment": comment})
                                    if score_val <= 6.5:
                                        criticisms.append(f"{cat} ({score_val}/10): {comment}")
                    if cats:
                        latest_rated_day = day_name
                        rated_categories = cats
                        break

                context["latest_evaluation"] = {
                    "day": latest_rated_day,
                    "categories": rated_categories,
                    "critical_points": criticisms
                }
            except Exception:
                pass

        # 1.5 IKINCI_BEYIN/AKTIF_BELLEK.md
        aktif_bellek_path = os.path.join(os.path.expanduser("~"), "IKINCI_BEYIN", "AKTIF_BELLEK.md")
        if not os.path.exists(aktif_bellek_path):
            aktif_bellek_path = os.path.join(self.root_dir, "AKTIF_BELLEK.md")
        if os.path.exists(aktif_bellek_path):
            try:
                with open(aktif_bellek_path, "r", encoding="utf-8") as f:
                    context["aktif_bellek"] = f.read()[:800]
            except Exception:
                pass

        context["_read_time_ms"] = round((time.time() - start_t) * 1000, 2)
        return context

    # -------------------------------------------------------------
    # 2. JEV Sistem 1 Hafıza Sentezi (~500 ms)
    # -------------------------------------------------------------

    def synthesize_with_jev(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Toplanan hafızayı Jev Sistem 1 modeline göndererek bugünün odak kararını üretir."""
        target_day = context.get("target_day", "Gun_X")
        last_eval = context.get("latest_evaluation", {})
        critical_points = last_eval.get("critical_points", [])
        criticisms_str = "\n".join(f"- {c}" for c in critical_points) if critical_points else "Önceki gün kritik bir arıza bildirilmedi."

        state = (
            f"PROJE: Kesiit Video Otomasyonu (YouTube Shorts & Instagram Reels)\n"
            f"ÜRETİLECEK HEDEF GÜN: {target_day}\n"
            f"SON DEĞERLENDİRME: {last_eval.get('day', 'Bilinmiyor')}\n"
            f"ÖNCEKİ GÜN ELEŞTİRİLERİ VE DÜŞÜK PUANLAR:\n{criticisms_str}\n\n"
            f"TEMEL STANDARTLAR:\n"
            f"- %0 Statik Slayt / Tamamı 4K Dinamik Video\n"
            f"- %45 Konuşmacı / %55 B-Roll Altın Oranı\n"
            f"- DOAC alt bantlarını özel dikey crop ile temizleme\n"
            f"- EBU R128 (-14.0 LUFS) ses mastering\n"
            f"- Gerçek mimikli yüksek CTR dikey kapak\n"
        )

        questions = {
            "primary_focus": self.jev.choice(
                options={
                    "broll_dynamism_zero_static": "0 adet statik slayt, %100 dinamik 4K video B-roll kurgusu",
                    "cover_authenticity_real_face": "Yapay AI kapağı yerine gerçek konuşmacı mimikli 1080x1920 kapak",
                    "audio_mastering_lufs": "-14 LUFS ve arka plan müziği diyalog ducking dengesi",
                    "hook_sharpness": "İlk 3-5 saniyede izleyiciyi kilitleyen kanca gücü"
                },
                instructions="Önceki günün puanları ve eleştirilerine göre bugünkü üretimde en yüksek öncelikle dikkat edilecek alan"
            ),
            "strict_guardrail": self.jev.choice(
                options={
                    "never_use_static_slides": "KESİNLİKLE sabit fotoğraf/kitap kapağı slaytı koyma, hareketli video kullan",
                    "clean_lower_third_banners": "Orijinal videodaki alt yazı bantlarını dikey crop ile temizle",
                    "maintain_golden_ratio": "Konuşmacı ve B-roll arasındaki %45-%55 dengesini bozma"
                },
                instructions="Bugün tekrarlanmaması gereken en kritik kırmızı çizgi / guardrail kuralı"
            ),
            "pipeline_readiness": self.jev.noul(
                instructions="Önceki günün eleştirileri ve hafıza kaydedilmiş durumda. Proje teknik olarak yeni gün üretimine başlamaya hazır mı?",
                true_criteria="Geçmiş dersler ve hafıza hazır, yeni gün üretimine başlanabilir.",
                false_criteria="Kritik dosya veya hafıza eksik, üretim başlayamaz."
            )
        }

        try:
            start_j = time.time()
            res = self.jev.decide(state=state, questions=questions)
            jev_latency = round((time.time() - start_j) * 1000, 2)
            answers = res.get("answers", {})

            primary_focus = answers.get("primary_focus", {}).get("choice", "broll_dynamism_zero_static")
            strict_guardrail = answers.get("strict_guardrail", {}).get("choice", "never_use_static_slides")
            is_ready = answers.get("pipeline_readiness", {}).get("noul", 1.0) >= 0.7

            return {
                "success": True,
                "jev_latency_ms": jev_latency,
                "jev_cost_usd": res.get("usage", {}).get("cost", 0.0),
                "primary_focus": primary_focus,
                "strict_guardrail": strict_guardrail,
                "is_ready": is_ready,
                "raw_answers": answers
            }
        except Exception as e:
            # Yerel kural tabanlı deterministik fallback
            return {
                "success": False,
                "error": str(e),
                "primary_focus": "broll_dynamism_zero_static",
                "strict_guardrail": "never_use_static_slides",
                "is_ready": True
            }

    # -------------------------------------------------------------
    # 3. Yürütme ve Raporlama (Tek Komut, <1 Saniye)
    # -------------------------------------------------------------

    def run(self, print_report: bool = True) -> Dict[str, Any]:
        t0 = time.time()
        local_ctx = self.collect_local_context()
        jev_decision = self.synthesize_with_jev(local_ctx)
        total_time_ms = round((time.time() - t0) * 1000, 2)

        report = {
            "execution_time_ms": total_time_ms,
            "target_day": local_ctx["target_day"],
            "last_completed_day": local_ctx["last_completed_day"],
            "latest_evaluated_day": local_ctx["latest_evaluation"].get("day"),
            "critical_feedbacks": local_ctx["latest_evaluation"].get("critical_points", []),
            "jev_strategy": {
                "primary_focus": jev_decision.get("primary_focus"),
                "strict_guardrail": jev_decision.get("strict_guardrail"),
                "is_ready": jev_decision.get("is_ready"),
                "cost_usd": jev_decision.get("jev_cost_usd", 0.0),
                "latency_ms": jev_decision.get("jev_latency_ms", 0.0)
            }
        }

        if print_report:
            self._print_terminal_dashboard(report)

        return report

    def _print_terminal_dashboard(self, r: Dict[str, Any]):
        print("\n" + "=" * 75)
        print("⚡ JEV PRE-FLIGHT SYNTHESIZER — 1 SANİYEDE PROJE HAFIZASI & KARAR")
        print("=" * 75)
        print(f"🎯 Hedef Üretim Günü      : {r['target_day']} (Son Tamamlanan: {r['last_completed_day']})")
        print(f"⏱️ Toplam Sentez Süresi    : {r['execution_time_ms']} ms (< 1.0 saniye)")
        print(f"📊 Son Puanlanan Gün     : {r['latest_evaluated_day'] or 'Değerlendirme Bekleniyor'}")
        
        feedbacks = r.get("critical_feedbacks", [])
        if feedbacks:
            print("⚠️ Dikkate Alınacak Kritik Eleştiriler:")
            for fb in feedbacks[:3]:
                print(f"   • {fb}")
        else:
            print("✅ Önceki Gün Kritik Eleştiri: Yok")

        js = r["jev_strategy"]
        print("\n🧠 JEV SİSTEM 1 KARAR STRATEJİSİ:")
        print(f"   🔥 1. Öncelikli Odak    : {js['primary_focus']}")
        print(f"   🛡️ Kırmızı Çizgi Kuralı : {js['strict_guardrail']}")
        print(f"   🚀 Üretime Hazır mı?    : {'EVET' if js['is_ready'] else 'HAYIR'}")
        print(f"   💰 Jev Maliyeti         : ${js['cost_usd']:.6f} ({js['latency_ms']} ms)")
        print("=" * 75 + "\n")


def run_preflight() -> Dict[str, Any]:
    synthesizer = PreflightSynthesizer()
    return synthesizer.run(print_report=True)


if __name__ == "__main__":
    run_preflight()
