"""
tests/test_viral_radar_90_threshold.py — ViralRadar 90+ Eşik Döngüsü Unittest Paketi
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.viral_radar import ViralRadar


class TestViralRadar90Threshold(unittest.TestCase):
    """ViralRadar 90+ eşik denetimi ve çok turlu genişleme döngüsü testleri."""

    def setUp(self):
        self.radar = ViralRadar(target_valid_transcripts=2, mode="shorts", min_score=90.0, max_rounds=3)

    @patch.object(ViralRadar, "collect_transcripts")
    @patch.object(ViralRadar, "evaluate_window_with_jev")
    @patch.object(ViralRadar, "generate_candidate_windows")
    def test_01_loops_until_90_reached(self, mock_gen_windows, mock_eval_jev, mock_collect):
        """Puan < 90 olduğunda aramanın devam ettiğini, >= 90 olunca şampiyonla durduğunu doğrular."""
        # Simülasyon:
        # Tur 1: Transkript gelir, pencere puanı 74.5 döner (< 90).
        # Tur 2: Yeni transkript gelir, pencere puanı 93.2 döner (>= 90).
        
        mock_collect.side_effect = [
            [{"id": "v1", "title": "Video 1", "url": "http://v1", "vtt_path": "v1.vtt"}],
            [{"id": "v2", "title": "Video 2", "url": "http://v2", "vtt_path": "v2.vtt"}]
        ]
        
        mock_gen_windows.return_value = [{
            "start": 10.0, "end": 40.0, "duration": 30.0,
            "hook_text": "Kanca", "punchline_text": "Vuruş", "full_text": "Konuşma metni"
        }]

        mock_eval_jev.side_effect = [
            # Tur 1 sonucu: 74.5 (Yetersiz)
            {
                "start": 10.0, "end": 40.0, "duration": 30.0,
                "hook_text": "Kanca", "punchline_text": "Vuruş", "full_text": "Metin 1",
                "scores": {
                    "hook_prob": 0.7, "standalone_prob": 0.6,
                    "topic_score": 3.5, "viral_score": 3.0,
                    "composite_score": 74.5
                }
            },
            # Tur 2 sonucu: 93.2 (90+ Başarılı!)
            {
                "start": 15.0, "end": 45.0, "duration": 30.0,
                "hook_text": "Muazzam Kanca", "punchline_text": "Efsane Vuruş", "full_text": "Metin 2",
                "scores": {
                    "hook_prob": 0.95, "standalone_prob": 0.9,
                    "topic_score": 4.8, "viral_score": 4.7,
                    "composite_score": 93.2
                }
            }
        ]

        with patch("engine.candidate_ranker.CandidateRanker.parse_vtt", return_value=[{"start": 0, "end": 10, "text": "t"}]):
            manifest = self.radar.hunt_best_clip(
                topic="test_topic",
                min_score=90.0,
                max_rounds=3
            )

        self.assertEqual(manifest["total_rounds_executed"], 2, "Tur 1'de 74.5 alan radar Tur 2'ye geçmelidir.")
        self.assertTrue(manifest["meets_quality_threshold"], "90+ puan sağlandığı için True olmalıdır.")
        self.assertEqual(manifest["champion"]["scores"]["composite_score"], 93.2)
        self.assertEqual(manifest["champion"]["source_video_id"], "v2")

    @patch.object(ViralRadar, "collect_transcripts")
    @patch.object(ViralRadar, "evaluate_window_with_jev")
    @patch.object(ViralRadar, "generate_candidate_windows")
    def test_02_max_rounds_fallback_when_never_reaches_90(self, mock_gen_windows, mock_eval_jev, mock_collect):
        """Hiçbir aday 90'a ulaşamadığında max_rounds sonunda en iyi adayın seçildiğini doğrular."""
        mock_collect.side_effect = [
            [{"id": "v1", "title": "Video 1", "url": "http://v1", "vtt_path": "v1.vtt"}],
            [{"id": "v2", "title": "Video 2", "url": "http://v2", "vtt_path": "v2.vtt"}]
        ]
        mock_gen_windows.return_value = [{
            "start": 0.0, "end": 30.0, "duration": 30.0,
            "hook_text": "Kanca", "punchline_text": "Vuruş", "full_text": "Metin"
        }]
        mock_eval_jev.side_effect = [
            {"start": 0, "end": 30, "duration": 30, "hook_text": "h", "punchline_text": "p", "full_text": "t",
             "scores": {"composite_score": 65.0, "hook_prob": 0.6, "standalone_prob": 0.5}},
            {"start": 0, "end": 30, "duration": 30, "hook_text": "h", "punchline_text": "p", "full_text": "t",
             "scores": {"composite_score": 82.0, "hook_prob": 0.8, "standalone_prob": 0.7}}
        ]

        with patch("engine.candidate_ranker.CandidateRanker.parse_vtt", return_value=[{"start": 0, "end": 10, "text": "t"}]):
            manifest = self.radar.hunt_best_clip(
                topic="test_topic",
                min_score=90.0,
                max_rounds=2
            )

        self.assertEqual(manifest["total_rounds_executed"], 2)
        self.assertFalse(manifest["meets_quality_threshold"], "90 eşiğine ulaşılamadığı için False olmalıdır.")
        self.assertEqual(manifest["champion"]["scores"]["composite_score"], 82.0, "En yüksek aday seçilmelidir.")


if __name__ == "__main__":
    unittest.main()
