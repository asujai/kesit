"""
core/jev_client.py — Jev (TypeSafe AI) Sistem 1 Karar Motoru İstemcisi
OpenRouter Decisions API (~typesafe/jev-latest) üzerinden hızlı, tip güvenli,
doğrulamalı, önbellekli ve dayanıklı karar alma motoru.
"""

import os
import json
import time
import hashlib
import requests
from typing import Dict, Any, List, Optional, Union

OPENROUTER_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_JEV_MODEL = "~typesafe/jev-latest"

def get_openrouter_api_key() -> str:
    """Proje kökündeki .env veya ortam değişkeninden OPENROUTER_API_KEY'i çeker."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('OPENROUTER_API_KEY='):
                    return line.split('=', 1)[1].strip(' "\'')
    return os.environ.get('OPENROUTER_API_KEY', '')


class JevValidationError(Exception):
    """Jev API yanıtı beklenen şema veya tip kurallarına uymadığında fırlatılır."""
    pass


class JevClient:
    """
    TypeSafe AI Jev modeli için OpenRouter Decisions istemcisi.
    Gelişmiş özellikler:
      - Yanıt doğrulama ve tip denetimi
      - 0-tabanlı skor normalizasyonu (1-5 ölçeği desteği)
      - İçerik hash'li yerel önbellek (aynı durum/soru tekrar çağrılmaz)
      - Üstel geri çekilme (exponential backoff) ile otomatik tekrar deneme
      - Oturum bazlı maliyet takibi ve bütçe tavanı kontrolü
      - Düşük güven (low confidence) uyarı mekanizması
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_JEV_MODEL,
        max_retries: int = 3,
        timeout: int = 15,
        budget_limit_usd: float = 1.0,
        enable_cache: bool = True,
        cache_dir: Optional[str] = None
    ):
        self.api_key = api_key or get_openrouter_api_key()
        self.model = model
        self.endpoint = OPENROUTER_DECISIONS_URL
        self.max_retries = max_retries
        self.timeout = timeout
        self.budget_limit_usd = budget_limit_usd
        self.enable_cache = enable_cache

        self.total_cost_usd = 0.0
        self.total_requests = 0
        self.cache_hits = 0

        # Önbellek dizini
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', '.cache')
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(self.cache_dir, 'jev_cache.json')
        self._memory_cache: Dict[str, Any] = {}
        self._load_cache()

    # -------------------------------------------------------------
    # Önbellek & Güvenlik
    # -------------------------------------------------------------

    def _load_cache(self):
        """Yerel önbellek dosyasını okur."""
        if not self.enable_cache:
            return
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._memory_cache = json.load(f)
        except Exception:
            self._memory_cache = {}

    def _save_cache(self):
        """Yerel önbellek dosyasına yazar."""
        if not self.enable_cache:
            return
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._memory_cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _compute_cache_key(self, state: str, questions: Dict[str, Any]) -> str:
        """State, model ve sorulardan benzersiz SHA-256 hash üretir."""
        raw = json.dumps({
            "model": self.model,
            "state": state,
            "questions": questions
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    # -------------------------------------------------------------
    # Karar İlkelleri (Primitives)
    # -------------------------------------------------------------

    @staticmethod
    def noul(instructions: str, true_criteria: str = "Evet / Doğru / Uygun", false_criteria: str = "Hayır / Yanlış / Uygun Değil") -> Dict[str, Any]:
        """Evet / Hayır (0.0 - 1.0 arası kalibre edilmiş olasılık) kararı."""
        return {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": true_criteria,
                "false": false_criteria
            }
        }

    @staticmethod
    def choice(options: Union[List[str], Dict[str, str]], instructions: str) -> Dict[str, Any]:
        """Verilen seçenekler arasından en uygununu seçme kararı."""
        if isinstance(options, list):
            criteria_dict = {opt: opt for opt in options}
        else:
            criteria_dict = options

        return {
            "type": "choice",
            "instructions": instructions,
            "criteria": criteria_dict
        }

    @staticmethod
    def score(rubric: List[str], instructions: str) -> Dict[str, Any]:
        """
        Sıralı rubrik veya puan skalasında derecelendirme kararı.
        NOT: TypeSafe score ilkesi 0-tabanlıdır (rubric listesi N elemanlıysa 0..N-1 indeks döner).
        """
        return {
            "type": "score",
            "instructions": instructions,
            "criteria": rubric
        }

    # -------------------------------------------------------------
    # Yanıt Doğrulama (Response Validation)
    # -------------------------------------------------------------

    def _validate_response(self, res_json: Dict[str, Any], questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gelen JSON yanıtını şemaya ve soru tiplerine göre katı şekilde doğrular.
        Eksik, geçersiz veya bozuk yanıtları reddeder.
        """
        if not isinstance(res_json, dict):
            raise JevValidationError("Jev API yanıtı bir JSON nesnesi değil!")

        answers = res_json.get("answers")
        if not isinstance(answers, dict):
            raise JevValidationError(f"Jev yanıtında 'answers' sözlüğü bulunamadı! Ham yanıt: {res_json}")

        for q_name, q_spec in questions.items():
            if q_name not in answers:
                raise JevValidationError(f"Soru '{q_name}' için cevap bulunamadı!")

            ans = answers[q_name]
            q_type = q_spec.get("type")

            if q_type == "noul":
                prob = ans.get("noul")
                if prob is None or not (0.0 <= prob <= 1.0):
                    raise JevValidationError(f"'{q_name}' (noul) için geçerli 0.0-1.0 olasılık dönmedi: {prob}")

            elif q_type == "choice":
                chosen = ans.get("choice")
                valid_options = list(q_spec.get("criteria", {}).keys())
                if chosen not in valid_options:
                    raise JevValidationError(f"'{q_name}' (choice) sonucu ({chosen}) geçerli seçenekler arasında yok: {valid_options}")

            elif q_type == "score":
                raw_score = ans.get("score")
                levels_count = len(q_spec.get("criteria", []))
                if raw_score is None or not (0.0 <= raw_score <= (levels_count - 1 + 0.5)):
                    raise JevValidationError(f"'{q_name}' (score) için geçersiz ham skor: {raw_score}")

                # 1-5 normalizasyonu ekle (eğer 5 seviyeli rubrikse)
                ans["normalized_1_to_5"] = round(raw_score + 1.0, 2)

        return res_json

    # -------------------------------------------------------------
    # İcra / Çağrı Motoru (Decide)
    # -------------------------------------------------------------

    def decide(self, state: str, questions: Dict[str, Dict[str, Any]], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Durum (state) ve soruları Jev modeline gönderir.
        Önbellek, tekrar deneme, bütçe denetimi ve katı şema doğrulamasını işletir.
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY bulunamadı! Lütfen .env dosyasına ekleyin.")

        if self.total_cost_usd >= self.budget_limit_usd:
            raise RuntimeError(f"Jev bütçe tavanına ({self.budget_limit_usd}$) ulaşıldı! Mevcut harcama: ${self.total_cost_usd:.4f}")

        # 1. Önbellek kontrolü
        cache_key = self._compute_cache_key(state, questions)
        if self.enable_cache and cache_key in self._memory_cache:
            self.cache_hits += 1
            cached_data = dict(self._memory_cache[cache_key])
            cached_data["_cached"] = True
            return cached_data

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kesiit.pipeline",
            "X-OpenRouter-Title": "Kesiit Video Pipeline"
        }

        payload = {
            "model": self.model,
            "state": state,
            "questions": questions
        }

        req_timeout = timeout or self.timeout
        delay = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=req_timeout)
                duration_ms = (time.time() - start_time) * 1000

                # Hız sınırı (429) veya sunucu hatası (5xx) için tekrar dene
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt == self.max_retries:
                        raise RuntimeError(f"OpenRouter Jev Hatası ({response.status_code}) max deneme sonrası: {response.text}")
                    time.sleep(delay)
                    delay *= 2.0
                    continue

                if response.status_code != 200:
                    raise RuntimeError(f"OpenRouter Jev İstek Hatası ({response.status_code}): {response.text}")

                res_json = response.json()
                validated = self._validate_response(res_json, questions)
                validated["_latency_ms"] = round(duration_ms, 2)
                validated["_cached"] = False

                # Maliyet takibi
                cost = validated.get("usage", {}).get("cost", 0.0)
                self.total_cost_usd += float(cost)
                self.total_requests += 1

                # Önbelleğe kaydet
                if self.enable_cache:
                    self._memory_cache[cache_key] = validated
                    self._save_cache()

                return validated

            except (requests.exceptions.RequestException, JevValidationError) as e:
                if attempt == self.max_retries:
                    raise
                time.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"Jev karar motoru {self.max_retries} denemeden sonra yanıt veremedi.")

    # -------------------------------------------------------------
    # Kesiit Video Pipeline Özel Alan Yardımcıları (Domain Helpers)
    # -------------------------------------------------------------

    def evaluate_viral_candidate(self, chunk_text: str) -> Dict[str, Any]:
        """
        Bir transkript parçasını viral potansiyeli ve kanca gücü bakımından puanlar.
        Sorular:
          - is_strong_hook: noul (İlk 3-5s kanca gücü)
          - is_standalone: noul (Bağımsız anlaşılabilirlik)
          - viral_score: score (0-4 ham indeks, otomatik 1-5 normalizasyonu)
          - primary_emotion: choice (merak, surpriz, ilham, bilgi, monoton)
        """
        questions = {
            "is_strong_hook": self.noul(
                instructions="İlk 3-5 saniyede izleyiciyi ekrana kilitleyecek güçlü bir kanca veya merak unsuru var mı?",
                true_criteria="Şoke edici, merak uyandıran veya ezber bozan güçlü bir giriş cümlesi var.",
                false_criteria="Sıradan, yavaş veya bağlam gerektiren düz bir konuşma."
            ),
            "is_standalone": self.noul(
                instructions="Bu konuşma parçası öncesi veya sonrası olmadan tek başına dinlendiğinde tam anlam ifade ediyor mu?",
                true_criteria="Bağımsız dinlendiğinde ana fikri ve mesajı eksiksiz anlaşılıyor.",
                false_criteria="Önceki cümleye atıfta bulunuyor veya yarım kalmış hissi veriyor."
            ),
            "viral_score": self.score(
                rubric=[
                    "0: Çok sönük, ilgi çekmeyen veya teknik monolog",
                    "1: Vasat, ortalama bir konuşma detayı",
                    "2: İlginç ama paylaşma isteği uyandırmıyor",
                    "3: Güçlü bir içgörü, yüksek etkileşim potansiyeli",
                    "4: Kesinlikle viral, şoke edici veya hayat dersi niteliğinde"
                ],
                instructions="Genel sosyal medya (Shorts/Reels) viral potansiyeli ve paylaşılabilirlik skoru (0..4)"
            ),
            "primary_emotion": self.choice(
                options={
                    "merak": "İzleyicide soru işareti ve gizem uyandıran anlatım",
                    "surpriz": "Ezber bozan, beklenmedik bilimsel gerçek veya şok",
                    "ilham": "Motive edici, hayatı sorgulatan felsefi içgörü",
                    "bilgi": "Net, eğitici ve pratik bir açıklama",
                    "monoton": "Düz, enerjisi düşük akademik açıklama"
                },
                instructions="Bu kesitin izleyicide uyandırdığı baskın his"
            )
        }
        return self.decide(state=chunk_text, questions=questions)

    def select_best_broll(self, sentence: str, broll_candidates: Dict[str, str], verify_match: bool = True) -> Dict[str, Any]:
        """
        Codex denetiminde belirtilen 'bağlamsız B-roll uyumu' sorununu çözen 2 adımlı veya tam durumlu seçim:
        Adım 1: Cümle ile tüm adayların açıklamaları state içinde karşılaştırılır ve 'choice' seçilir.
        Adım 2: Seçilen adayın açıklanması cümleyle doğrulanır (noul: is_proper_fit).
        """
        # Aday listesini state içine de açıkça gömüyoruz ki model tüm adayları aynı bağlamda görsün
        candidate_summary = "\n".join([f"- [{cid}]: {desc}" for cid, desc in broll_candidates.items()])
        full_state = f"Konuşmacının Cümlesi:\n\"{sentence}\"\n\nMevcut Görsel Adayları:\n{candidate_summary}"

        questions = {
            "selected_broll": self.choice(
                options=broll_candidates,
                instructions="Konuşmacının cümlesindeki kavramı, hissi veya eylemi en doğru yansıtan video/görsel adayının kimliği (ID)"
            )
        }

        res = self.decide(state=full_state, questions=questions)
        chosen_id = res["answers"]["selected_broll"]["choice"]
        chosen_desc = broll_candidates.get(chosen_id, "")

        if verify_match and chosen_desc:
            # 2. Adım: Seçilen aday ile cümlenin doğrudan uyumunun teyidi (izole durum sorunu çözüldü)
            verification_state = f"Cümle: \"{sentence}\"\nSeçilen Video Sahnesi: \"{chosen_desc}\""
            verification_questions = {
                "is_accurate_fit": self.noul(
                    instructions="Seçilen görsel sahnesi cümledeki anlatıyı veya metaforu gerçekten doğru yansıtıyor mu?",
                    true_criteria="Görsel ve cümle semantik olarak uyumlu, zıtlık veya absürtlük yok.",
                    false_criteria="Görsel alakasız, yanıltıcı veya anlamsız."
                )
            }
            v_res = self.decide(state=verification_state, questions=verification_questions)
            res["answers"]["is_accurate_fit"] = v_res["answers"]["is_accurate_fit"]

        return res


if __name__ == "__main__":
    client = JevClient()
    print(f"[JevClient] İstemci hazır. Önbellek dizini: {client.cache_dir}")
