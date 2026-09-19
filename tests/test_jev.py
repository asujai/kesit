"""
tests/test_jev.py — Jev (TypeSafe AI) Standart Unittest Doğrulama Paketi
"""

import sys
import os
import unittest

# Windows terminal UTF-8 desteği
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Proje kökünü sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.jev_client import JevClient, get_openrouter_api_key, JevValidationError


class TestJevIntegration(unittest.TestCase):
    """Jev istemcisi, şema doğrulaması ve karar mekanizması testleri."""

    @classmethod
    def setUpClass(cls):
        cls.api_key = get_openrouter_api_key()
        cls.client = JevClient(api_key=cls.api_key, enable_cache=True)

    def test_01_api_key_configured(self):
        """API anahtarının .env dosyasında tanımlı olduğunu doğrular (maskeli kontrol)."""
        self.assertTrue(bool(self.api_key), "OPENROUTER_API_KEY .env dosyasında tanımlı olmalıdır.")
        self.assertTrue(self.api_key.startswith("sk-or-v1-"), "OpenRouter API anahtarı formatı geçersiz.")

    def test_02_validation_rejects_malformed_response(self):
        """İstemcinin bozuk veya şemaya uymayan yanıtları kesinlikle reddettiğini doğrular."""
        bad_response = {
            "answers": {
                "is_hook": {"type": "noul", "noul": 1.5} # 0-1 aralığı dışında geçersiz!
            }
        }
        questions = {"is_hook": {"type": "noul"}}
        with self.assertRaises(JevValidationError):
            self.client._validate_response(bad_response, questions)

    def test_03_score_normalization(self):
        """0-tabanlı ham skorun 1-5 aralığına doğru normalleştirildiğini doğrular."""
        mock_score_res = {
            "answers": {
                "viral_score": {"type": "score", "score": 2.5}
            }
        }
        questions = {"viral_score": {"type": "score", "criteria": ["0", "1", "2", "3", "4"]}}
        validated = self.client._validate_response(mock_score_res, questions)
        self.assertEqual(validated["answers"]["viral_score"]["normalized_1_to_5"], 3.5)

    def test_04_cache_computation(self):
        """Aynı girdi için üretilen önbellek anahtarının deterministik olduğunu doğrular."""
        k1 = self.client._compute_cache_key("test_state", {"q": {"type": "noul"}})
        k2 = self.client._compute_cache_key("test_state", {"q": {"type": "noul"}})
        self.assertEqual(k1, k2, "Önbellek anahtarı deterministik olmalıdır.")


if __name__ == "__main__":
    unittest.main()
