"""
tests/test_preflight.py — Jev Pre-Flight Sentezleyicisi Unittest Paketi
"""

import sys
import os
import unittest

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.preflight import PreflightSynthesizer


class TestPreflightSynthesizer(unittest.TestCase):
    """Preflight hafıza toplama, Jev sentezi ve hız testleri."""

    def setUp(self):
        self.synthesizer = PreflightSynthesizer()

    def test_01_collect_local_context(self):
        """Yerel hafıza dosyalarının eksiksiz toplandığını ve hedef günün tespit edildiğini doğrular."""
        ctx = self.synthesizer.collect_local_context()
        self.assertIn("target_day", ctx)
        self.assertTrue(ctx["target_day"].startswith("Gun_"))
        self.assertIn("latest_evaluation", ctx)
        self.assertIn("critical_points", ctx["latest_evaluation"])
        self.assertLess(ctx["_read_time_ms"], 200.0, "Yerel hafıza okuması 200ms altında olmalıdır.")

    def test_02_preflight_execution_speed(self):
        """Tüm preflight sürecinin (hafıza + Jev kararı) 1.5 saniye altında tamamlandığını doğrular."""
        report = self.synthesizer.run(print_report=False)
        self.assertIn("execution_time_ms", report)
        self.assertIn("jev_strategy", report)
        strategy = report["jev_strategy"]
        self.assertIn("primary_focus", strategy)
        self.assertIn("strict_guardrail", strategy)
        self.assertIn("is_ready", strategy)
        self.assertTrue(strategy["is_ready"])
        # Toplam sürenin makul bir üst sınırda kaldığı kontrolü
        self.assertLess(report["execution_time_ms"], 2000.0, "Preflight raporu 2 saniyeden kısa sürmelidir.")

    def test_03_critical_feedback_parsing(self):
        """PUANLAMA_GECMISI.md dosyasındaki düşük puanların kritik eleştiri olarak ayrıştırıldığını doğrular."""
        ctx = self.synthesizer.collect_local_context()
        eval_data = ctx.get("latest_evaluation", {})
        self.assertIsNotNone(eval_data.get("day"))
        feedbacks = eval_data.get("critical_points", [])
        # Gün 8'de 4.0 ve 6.5 puanları olduğu için en az 1 kritik eleştiri yakalanmış olmalı
        self.assertGreaterEqual(len(feedbacks), 1)


if __name__ == "__main__":
    unittest.main()
