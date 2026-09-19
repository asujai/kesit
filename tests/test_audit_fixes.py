import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.candidate_ranker import CandidateRanker
from core.semantic_selector import SemanticSelector, VisualNeed
from core.asset_registry import AssetRegistry
from engine.fidelity import SemanticFidelityChecker
from engine.timeline import TimelineCompiler
from engine.spec import VideoSpec
from engine.audio_engine import AudioEngine
from engine.quality_gate import QualityGate

class TestAuditFixes(unittest.TestCase):
    """
    Behavioral Test Suite covering all audit requirements:
    1. CandidateRanker: Timeline steering, boundary clamping, and VTT subtitle resync.
    2. SemanticSelector: Avoid deduction, circular query bias removal, and in-flight reservation.
    3. AssetRegistry: SHA-256 deduplication and blacklist rejection.
    4. SemanticFidelityChecker: Granular attribution/qualification, false qualifier removal, and missing transcript rejection.
    5. AudioEngine & Loudness: Parameter-based caching, mtime sensitivity, and strict loudness gate behavior.
    6. QualityGate: Strict cover verification gating and transactional staging with rollback.
    7. Speaker Cut Fallback: Two-stage validation and overlay exclusion in TimelineCompiler.
    """

    def test_01_candidate_ranker_drives_timeline_and_subtitles(self):
        """Verify candidate selection dynamically updates in/out points, duration, cuts, and subtitles."""
        spec_dict = {
            "meta": {"day": "Gun_Test"},
            "source": {
                "raw_video_path": "dummy.mp4",
                "in_point": 0.0,
                "out_point": 50.0
            },
            "audio": {},
            "cuts": [
                {"id": "cut_early", "start_t": 2.0, "end_t": 6.0},
                {"id": "cut_overlap", "start_t": 8.0, "end_t": 20.0},
                {"id": "cut_late", "start_t": 22.0, "end_t": 30.0}
            ],
            "subtitles": []
        }

        # Candidate window: 100.0s -> 115.0s (duration = 15.0s)
        candidate = {
            "id": "cand_100.0_115.0",
            "start": 100.0,
            "end": 115.0,
            "duration": 15.0
        }

        with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False, encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            f.write("00:01:30.000 --> 00:01:35.000\nOld pre-cue\n\n")
            f.write("00:01:42.000 --> 00:01:46.000\nFirst cue inside candidate window\n\n")
            f.write("00:01:48.000 --> 00:01:52.000\nSecond cue inside candidate window\n\n")
            f.write("00:02:00.000 --> 00:02:05.000\nPost-candidate cue\n\n")
            vtt_tmp = f.name

        try:
            CandidateRanker.apply_candidate_to_spec(spec_dict, candidate, vtt_path=vtt_tmp)

            # 1. Check boundaries & duration
            self.assertEqual(spec_dict["source"]["in_point"], 100.0)
            self.assertEqual(spec_dict["source"]["out_point"], 115.0)
            self.assertEqual(spec_dict["source"]["duration"], 15.0)

            # 2. Check cuts: cut_early (2-6s) remains, cut_overlap (8-20s) is clamped to 15s, cut_late (22-30s) is dropped
            cut_ids = [c["id"] for c in spec_dict["cuts"]]
            self.assertIn("cut_early", cut_ids)
            self.assertIn("cut_overlap", cut_ids)
            self.assertNotIn("cut_late", cut_ids)

            overlap_cut = next(c for c in spec_dict["cuts"] if c["id"] == "cut_overlap")
            self.assertEqual(overlap_cut["end_t"], 15.0, "Cut extending past new duration must be clamped")

            # 3. Check subtitles: Only cues between 100.0 and 115.0 are extracted and resynchronized relative to 0.0
            subs = spec_dict["subtitles"]
            self.assertEqual(len(subs), 2, "Exactly 2 cues fall within 100-115s window")
            self.assertEqual(subs[0]["start"], 2.0)   # 102.0 - 100.0
            self.assertEqual(subs[0]["end"], 6.0)     # 106.0 - 100.0
            self.assertEqual(subs[0]["text"], "First cue inside candidate window")
            self.assertEqual(subs[1]["start"], 8.0)   # 108.0 - 100.0
            self.assertEqual(subs[1]["end"], 12.0)    # 112.0 - 100.0
            self.assertEqual(subs[1]["text"], "Second cue inside candidate window")
        finally:
            if os.path.exists(vtt_tmp):
                os.remove(vtt_tmp)

    def test_02_semantic_selector_scoring_and_active_reservations(self):
        """Verify avoid penalty, circular bias elimination, and active reservation tracking."""
        selector = SemanticSelector()
        v_need = VisualNeed(
            scene_id="c01",
            spoken_text="Sabah kalktığında elin telefona gidiyor",
            subject_action="waking up in bed reaching for phone",
            environment="dark bedroom night morning",
            emotion="tired distracted",
            media_type="video",
            avoid=["3d", "animation", "cartoon", "render"],
            queries=["bedroom morning phone"],
            required_duration=3.0
        )

        # 1. Avoid keyword penalty test
        bad_cand = {
            "id": "cand_bad_3d",
            "provider": "pexels",
            "duration": 5.0,
            "width": 1080,
            "height": 1920,
            "tags": "3d render, cartoon boy waking up",
            "title": "Cartoon Sleeping",
            "download_url": "http://example.com/bad.mp4"
        }
        res_bad = selector.score_candidate(bad_cand, v_need, current_day="Gun_Test", query="bedroom morning phone")
        self.assertLess(res_bad["score"], 0.0, "Triggering avoid keywords must heavily penalize the score")

        # 2. Circular bias test: Candidate with unrelated tags must NOT get bonus from query terms
        irrelevant_cand = {
            "id": "cand_irrelevant",
            "provider": "pexels",
            "duration": 5.0,
            "width": 1080,
            "height": 1920,
            "tags": "sunny tropical beach ocean waves surfing",
            "title": "Tropical Beach Surfing",
            "download_url": "http://example.com/beach.mp4"
        }
        res_irrelevant = selector.score_candidate(irrelevant_cand, v_need, current_day="Gun_Test", query="bedroom morning phone")

        # 3. Active reservation test: Once selected in current run, same asset cannot be selected again
        good_cand = {
            "id": "cand_good_01",
            "provider": "pexels",
            "duration": 6.0,
            "width": 1080,
            "height": 1920,
            "tags": "man waking up bed reaching for smartphone bedroom",
            "title": "Person waking up and checking smartphone in bedroom",
            "download_url": "http://example.com/good.mp4"
        }
        score_good = selector.score_candidate(good_cand, v_need, current_day="Gun_Test", query="bedroom morning phone")
        self.assertGreater(score_good["score"], 6.0)
        self.assertLess(res_irrelevant["score"], score_good["score"] - 5.0, "Irrelevant asset must score significantly lower than compliant asset")

        # Reserve it
        selector.active_reservations.add("cand_good_01")
        score_reserved = selector.score_candidate(good_cand, v_need, current_day="Gun_Test", query="bedroom morning phone")
        self.assertLess(score_reserved["score"], 0.0, "Already reserved asset in active run must be heavily penalized")

    def test_03_asset_registry_hash_collision_and_blacklist(self):
        """Verify content hash deduplication across downloads and blacklist rejections."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            reg_path = os.path.join(tmp_dir, "registry.json")
            reg = AssetRegistry(reg_path)

            file1 = os.path.join(tmp_dir, "clip1.mp4")
            with open(file1, "wb") as f:
                f.write(b"SAMPLE_VIDEO_DATA_001_A")

            file2 = os.path.join(tmp_dir, "clip2_duplicate.mp4")
            with open(file2, "wb") as f:
                f.write(b"SAMPLE_VIDEO_DATA_001_A") # Exact same bytes

            # Register file1
            reg.register_asset("pexels", "asset_100", "video", "Morning phone", "phone", file_path=file1)

            # Compute hash of file2 and check collision
            h2 = reg.compute_file_hash(file2)
            match = reg.find_asset_by_hash(h2)
            self.assertIsNotNone(match, "Duplicate file with identical hash must be detected")
            self.assertEqual(match["asset_id"], "asset_100")

            # Blacklist check
            reg.record_rejection("pexels", "asset_100", "phone", "Corrupted frame")
            self.assertTrue(reg.is_rejected("pexels", "asset_100"))

    def test_04_fidelity_gate_negative_and_positive(self):
        """Verify strict fidelity audit: no 'dokunuyoruz' loophole, mandatory attribution AND qualification, and transcript presence."""
        ref_transcript = "klinik psikolog beyhan budak gün içinde telefonla biraz fazlaca yakın olan bir insan günde 5000'den fazla kez ekranına dokunuyor"

        # Case A: Negative - Direct ungrounded claim without attribution or population qualifier
        pub_bad_1 = {
            "instagram": {
                "hook": "Günde tam 5.000 kez telefonuna dokunuyorsun! Farkında bile değilsin... 📱👇"
            }
        }
        res_a = SemanticFidelityChecker.audit_fidelity([], ref_transcript, pub_bad_1)
        self.assertFalse(res_a["passed"])
        self.assertTrue(any(v["type"] in ("UNATTRIBUTED_CLAIM_REJECTED", "DROPPED_QUALIFIER_REJECTED") for v in res_a["violations"]))

        # Case B: Negative - Using 'dokunuyoruz' without population scope qualifier (e.g. "yoğun kullanıcılar")
        pub_bad_2 = {
            "instagram": {
                "hook": "Günde 5.000 kez dokunuyoruz: Akıllı telefon bağımlılığı"
            }
        }
        res_b = SemanticFidelityChecker.audit_fidelity([], ref_transcript, pub_bad_2)
        self.assertFalse(res_b["passed"])
        self.assertTrue(any(v["type"] in ("UNATTRIBUTED_CLAIM_REJECTED", "DROPPED_QUALIFIER_REJECTED") for v in res_b["violations"]))

        # Case C: Negative - Missing transcript reference entirely
        pub_pos = {
            "instagram": {
                "hook": "Uzmanlar Uyarıyor: Yoğun telefon kullanıcıları günde 5.000 kez ekrana dokunuyor! 📱👇",
                "caption": "Klinik Psikolog Beyhan Budak çarpıcı bir gerçeğe parmak basıyor: Telefonla fazlaca yakın olan bir insan günde 5.000'den fazla kez ekrana dokunuyor."
            }
        }
        res_c = SemanticFidelityChecker.audit_fidelity([], "", pub_pos)
        self.assertFalse(res_c["passed"], "Audit must fail when transcript text is empty")
        self.assertTrue(any(v["type"] in ("MISSING_TRANSCRIPT_REJECTED", "MISSING_TRANSCRIPT_REFERENCE") for v in res_c["violations"]))

        # Case D: Positive - Attributed AND qualified claim with valid transcript reference
        res_d = SemanticFidelityChecker.audit_fidelity([], ref_transcript, pub_pos)
        self.assertTrue(res_d["passed"])
        self.assertEqual(len(res_d["violations"]), 0)

    def test_05_audio_engine_cache_invalidation_and_loudness_gate(self):
        """Verify parameter-based audio cache invalidation and QualityGate loudness checking."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_video = os.path.join(tmp_dir, "raw.mp4")
            with open(dummy_video, "wb") as f:
                f.write(b"DUMMY_VIDEO_STREAM")

            dummy_bgm = os.path.join(tmp_dir, "bgm.m4a")
            with open(dummy_bgm, "wb") as f:
                f.write(b"DUMMY_BGM_STREAM")

            dummy_master = os.path.join(tmp_dir, "master_audio.m4a")
            with open(dummy_master, "wb") as f:
                f.write(b"DUMMY_MASTER_AUDIO" * 500) # > 5000 bytes

            # 1. Compute baseline cache key
            key_v1 = AudioEngine.compute_audio_cache_key(
                raw_video=dummy_video, in_point=0.0, out_point=10.0,
                bgm_path=dummy_bgm, bgm_gain=0.14, target_lufs=-14.0, fade_out_duration=0.73
            )
            key_file = dummy_master + ".cache_key"
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(key_v1)

            # Assert cache is initially valid
            self.assertTrue(AudioEngine.is_audio_cache_valid(dummy_master, key_v1))

            # 2. Mutate bgm_gain (0.14 -> 0.22)
            key_v2 = AudioEngine.compute_audio_cache_key(
                raw_video=dummy_video, in_point=0.0, out_point=10.0,
                bgm_path=dummy_bgm, bgm_gain=0.22, target_lufs=-14.0, fade_out_duration=0.73
            )
            self.assertNotEqual(key_v1, key_v2, "Mutating bgm_gain must produce a different cache key")
            self.assertFalse(AudioEngine.is_audio_cache_valid(dummy_master, key_v2), "Old cached file must be invalid for new key")

            # 3. Test QualityGate loudness verification behavior via mock
            spec_mock = MagicMock()
            spec_mock.meta = {"day": "Gun_Test"}
            spec_mock.audio = {"target_lufs": -14.0}
            spec_mock.cuts = []
            spec_mock.subtitles = []
            spec_mock.publish = {}
            qgate = QualityGate(spec_mock, tmp_dir)

            # Sub-test: Out of tolerance LUFS (-12.5 LUFS vs -14.0 target)
            with patch.object(AudioEngine, "measure_loudness", return_value={"integrated_lufs": -12.5, "true_peak": -1.5}):
                with patch.object(qgate, "calculate_file_hash", return_value="a" * 64):
                    with patch("subprocess.run") as mock_subproc:
                        mock_subproc.return_value = MagicMock(returncode=0, stdout=json.dumps({
                            "streams": [{"width": 1080, "height": 1920, "duration": "10.0"}, {"duration": "10.0"}]
                        }))
                        with patch.object(qgate, "generate_and_verify_cover", return_value=True):
                            with patch.object(SemanticFidelityChecker, "audit_fidelity", return_value={"passed": True, "violations": [], "summary": "PASSED"}):
                                res = qgate.verify_and_release(dummy_video, transcript_text="sample transcript")
                                self.assertEqual(res["overall_status"], "FAILED")
                                self.assertTrue(any("Loudness out of spec" in f for f in res["failures"]))

    def test_06_quality_gate_cover_failure_and_transactional_rollback(self):
        """Verify cover generation failure aborts release, and deploy errors trigger clean rollback."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yt_dir = os.path.join(tmp_dir, "youtube", "Gun_Rollback")
            ig_dir = os.path.join(tmp_dir, "instagram", "Gun_Rollback")
            os.makedirs(yt_dir, exist_ok=True)
            os.makedirs(ig_dir, exist_ok=True)

            sentinel_file = os.path.join(yt_dir, "prior_release.txt")
            with open(sentinel_file, "w") as f:
                f.write("ORIGINAL_RELEASE_STATE")

            spec_mock = MagicMock()
            spec_mock.meta = {"day": "Gun_Rollback"}
            spec_mock.audio = {"target_lufs": -14.0}
            spec_mock.cuts = []
            spec_mock.subtitles = []
            spec_mock.publish = {"youtube": {}, "instagram": {}}
            qgate = QualityGate(spec_mock, tmp_dir)

            # 1. Test cover failure blocks delivery entirely
            dummy_master = os.path.join(tmp_dir, "master.mp4")
            with open(dummy_master, "wb") as f:
                f.write(b"MOCK_MASTER_STREAM")

            with patch.object(qgate, "calculate_file_hash", return_value="b" * 64):
                with patch("subprocess.run") as mock_subproc:
                    mock_subproc.return_value = MagicMock(returncode=0, stdout=json.dumps({
                        "streams": [{"width": 1080, "height": 1920, "duration": "10.0"}, {"duration": "10.0"}]
                    }))
                    with patch.object(AudioEngine, "measure_loudness", return_value={"integrated_lufs": -14.0, "true_peak": -1.5}):
                        with patch.object(SemanticFidelityChecker, "audit_fidelity", return_value={"passed": True, "violations": [], "summary": "PASSED"}):
                            with patch.object(qgate, "generate_and_verify_cover", return_value=False):
                                res_cover_fail = qgate.verify_and_release(dummy_master, transcript_text="sample")
                                self.assertEqual(res_cover_fail["overall_status"], "FAILED")
                                self.assertEqual(res_cover_fail["delivery_status"], "ABORTED")
                                self.assertTrue(any("cover thumbnail generation or verification failed" in f for f in res_cover_fail["failures"]))

            # 2. Test transactional rollback restoring previous directory on exception
            yt_staging = os.path.join(tmp_dir, "youtube", "Gun_Rollback.staging")
            ig_staging = os.path.join(tmp_dir, "instagram", "Gun_Rollback.staging")
            os.makedirs(yt_staging, exist_ok=True)
            os.makedirs(ig_staging, exist_ok=True)
            # Create dummy staging files
            with open(os.path.join(yt_staging, "Gun_Rollback_Shorts.mp4"), "wb") as f: f.write(b"A" * 200)
            with open(os.path.join(yt_staging, "Gun_Rollback_Shorts_Kapak.jpg"), "wb") as f: f.write(b"A" * 200)
            with open(os.path.join(yt_staging, "YOUTUBE_POST_BILGILERI.md"), "wb") as f: f.write(b"A" * 200)
            with open(os.path.join(ig_staging, "Gun_Rollback_Reels.mp4"), "wb") as f: f.write(b"A" * 200)
            # Missing INSTAGRAM_POST_BILGILERI.md to force transactional deployment exception

            ok = qgate._transactional_deploy(yt_staging, yt_dir, ig_staging, ig_dir)
            self.assertFalse(ok, "Deployment must fail when staging package is incomplete")
            self.assertTrue(os.path.exists(sentinel_file), "Original showcase files must be restored via rollback")
            with open(sentinel_file, "r") as f:
                self.assertEqual(f.read(), "ORIGINAL_RELEASE_STATE")

    def test_07_speaker_cut_fallback_and_timeline_exclusion(self):
        """Verify two-stage validation allows unresolved cuts and TimelineCompiler excludes speaker_cuts from overlays."""
        with tempfile.NamedTemporaryFile("w", suffix=".mp4", delete=False) as f:
            dummy_video = f.name

        spec_data = {
            "meta": {"day": "Gun_Test"},
            "source": {
                "raw_video_path": dummy_video,
                "in_point": 0.0,
                "out_point": 10.0
            },
            "audio": {},
            "cuts": [
                {
                    "id": "c01_unresolved",
                    "start_t": 2.0,
                    "end_t": 4.0,
                    "visual_need": {"spoken_text": "sample need"}
                }
            ],
            "subtitles": []
        }

        try:
            spec = VideoSpec.from_dict(spec_data)

            # Stage 1: allow_unresolved=True must PASS
            errors_initial = spec.validate(allow_unresolved=True)
            self.assertEqual(len(errors_initial), 0, "Unresolved cut with visual_need should pass initial validation")

            # Post-resolution validation before fallback or asset must FAIL
            errors_post = spec.validate_post_resolution()
            self.assertGreater(len(errors_post), 0, "Unresolved cut must fail post-resolution validation")

            # Revert to speaker cut fallback
            spec.cuts[0]["fallback"] = "speaker_cut"
            errors_fallback = spec.validate_post_resolution()
            self.assertEqual(len(errors_fallback), 0, "Cut with fallback='speaker_cut' must pass post-resolution validation")

            # Verify TimelineCompiler excludes speaker cut from normalized cuts
            compiler = TimelineCompiler(spec, os.path.dirname(dummy_video))
            normalized = compiler.collect_and_normalize_cuts()
            self.assertEqual(len(normalized), 0, "speaker_cut must be excluded from B-roll normalization and overlay")
        finally:
            if os.path.exists(dummy_video):
                os.remove(dummy_video)

    def test_08_candidate_ranker_rolling_dedup_and_context_completeness(self):
        """Verify rolling progressive VTT deduplication and context penalties for incomplete/dependent thoughts."""
        # 1. Test rolling progressive VTT deduplication
        raw_cues = [
            {"start": 0.0, "end": 2.5, "text": "Oraya katılamadım"},
            {"start": 2.0, "end": 4.5, "text": "Oraya katılamadım ve dediğimiz"},
            {"start": 4.0, "end": 6.5, "text": "dediğimiz şey aslında"}
        ]
        cleaned = CandidateRanker._deduplicate_rolling_cues(raw_cues)
        full_text = " ".join(c["text"] for c in cleaned)
        self.assertNotIn("katılamadım Oraya katılamadım", full_text, "Rolling prefix repetition must be removed")
        self.assertNotIn("dediğimiz dediğimiz", full_text, "Word-level suffix-prefix overlap must be deduplicated")

        # 2. Test context completeness scoring
        # Incomplete/dependent start ("Oraya katılamadım...") + dangling ending ("...şey aslında")
        score_dependent = CandidateRanker._score_context("Oraya katılamadım çünkü", "dediğimiz şey aslında", full_text="Oraya katılamadım çünkü dediğimiz şey aslında")
        self.assertLess(score_dependent, 4.0, "Dependent start and dangling conjunction end must be heavily penalized")

        # Complete standalone sentence with Turkish finite verb ending
        score_complete = CandidateRanker._score_context("İnsan bedeni hareket etmek için tasarlandı.", "Hareketsiz kaldığımızda metabolizma yavaşlıyor.", full_text="İnsan bedeni hareket etmek için tasarlandı. Hareketsiz kaldığımızda metabolizma yavaşlıyor.")
        self.assertGreater(score_complete, 7.0, "Standalone sentence with SOV finite verb and period must receive high score")

    def test_09_generic_fidelity_hedging_erosion_and_sensational_claims(self):
        """Verify generic fidelity checks: sensational verb rejection, hedging erosion, and cover text auditing."""
        transcript = "prof dr sinan canan insan belki onlarca kilometre yürümek için tasarlanmış bir bedene sahip ancak bütün gün oturuyoruz"

        # Case A: Sensational ungrounded claim ("çürütüyor")
        pub_sensational = {
            "youtube": {
                "title": "Tek Tıklamayla Yaşamak Beynimizi Nasıl Çürütüyor? | Sinan Canan"
            }
        }
        res_sens = SemanticFidelityChecker.audit_fidelity([], transcript, pub_sensational)
        self.assertFalse(res_sens["passed"])
        self.assertTrue(any(v["type"] == "UNGROUNDED_SENSATIONAL_CLAIM_REJECTED" for v in res_sens["violations"]))

        # Case B: Hedging erosion (transcript says "belki onlarca kilometre", pub stripped "belki")
        pub_eroded = {
            "youtube": {
                "description": "Günde onlarca kilometre yürümek için tasarlanmış bedenimiz..."
            }
        }
        res_eroded = SemanticFidelityChecker.audit_fidelity([], transcript, pub_eroded)
        self.assertFalse(res_eroded["passed"])
        self.assertTrue(any(v["type"] == "HEDGING_STRIPPED_REJECTED" for v in res_eroded["violations"]))

        # Case C: Cover text audit
        cover_bad = {
            "punch_line": "BEYNİN ÇÜRÜYOR!"
        }
        res_cover = SemanticFidelityChecker.audit_fidelity([], transcript, None, cover_data=cover_bad)
        self.assertFalse(res_cover["passed"])
        self.assertTrue(any(v["type"] == "UNGROUNDED_SENSATIONAL_CLAIM_REJECTED" for v in res_cover["violations"]))

        # Case D: Compliant text retaining hedge and faithful phrasing
        pub_faithful = {
            "youtube": {
                "title": "Her Şeyi Oturarak Yapmanın Bedeli | Prof. Dr. Sinan Canan",
                "description": "Prof. Dr. Sinan Canan anlatıyor: İnsan belki onlarca kilometre yürümek için tasarlanmış."
            }
        }
        res_faithful = SemanticFidelityChecker.audit_fidelity([], transcript, pub_faithful)
        self.assertTrue(res_faithful["passed"])

    def test_10_photo_duration_limit_and_subtitle_line_cap(self):
        """Verify static photos cannot exceed 3.0s (target 2.0s) and subtitle badges cannot exceed 2 lines."""
        # 1. Photo duration > 3.0s in spec validation
        spec_photo_bad = {
            "meta": {"day": "Gun_Test"},
            "source": {"raw_video_path": "dummy.mp4", "in_point": 0.0, "out_point": 10.0},
            "audio": {},
            "cuts": [
                {"id": "cut_long_photo", "media_type": "photo", "start_t": 2.0, "end_t": 6.5, "source_file": "dummy.jpg"}
            ],
            "subtitles": []
        }
        spec = VideoSpec.from_dict(spec_photo_bad)
        errors = spec.validate(allow_unresolved=True)
        self.assertTrue(any("exceeding strict limit of 3.0s" in e for e in errors), "Photo cut > 3.0s must be rejected by spec validation")

        # 2. Subtitle > 2 lines enforcement in SubtitleEngine
        from engine.subtitle_engine import SubtitleEngine
        sub_engine = SubtitleEngine(max_words=5)
        long_sentence = "Bu altyazı cümlesi çok uzun ve bir sürü kelime içerdiği için normalde üç veya dört satır tutabilir"
        lines = sub_engine.wrap_or_split_text(long_sentence)
        self.assertLessEqual(len(lines), 2, "Subtitle badge lines must strictly never exceed 2 lines")

    def test_11_fresh_day_transactional_rollback_cleans_promoted_dir(self):
        """Verify that on a brand new day release, if Instagram deployment fails after YouTube promotion, YouTube is completely cleaned up."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yt_dir = os.path.join(tmp_dir, "youtube", "Gun_NewFresh")
            ig_dir = os.path.join(tmp_dir, "instagram", "Gun_NewFresh")
            # Note: yt_dir and ig_dir do NOT exist beforehand! (brand new day)
            self.assertFalse(os.path.exists(yt_dir))
            self.assertFalse(os.path.exists(ig_dir))

            yt_staging = os.path.join(tmp_dir, "youtube", "Gun_NewFresh.staging")
            ig_staging = os.path.join(tmp_dir, "instagram", "Gun_NewFresh.staging")
            os.makedirs(yt_staging, exist_ok=True)
            os.makedirs(ig_staging, exist_ok=True)

            # Valid YouTube staging package
            with open(os.path.join(yt_staging, "Gun_NewFresh_Shorts.mp4"), "wb") as f: f.write(b"V" * 200)
            with open(os.path.join(yt_staging, "Gun_NewFresh_Shorts_Kapak.jpg"), "wb") as f: f.write(b"C" * 200)
            with open(os.path.join(yt_staging, "YOUTUBE_POST_BILGILERI.md"), "wb") as f: f.write(b"M" * 200)

            # Valid Instagram staging package
            with open(os.path.join(ig_staging, "Gun_NewFresh_Reels.mp4"), "wb") as f: f.write(b"V" * 200)
            with open(os.path.join(ig_staging, "INSTAGRAM_POST_BILGILERI.md"), "wb") as f: f.write(b"M" * 200)

            spec_mock = MagicMock()
            spec_mock.meta = {"day": "Gun_NewFresh"}
            spec_mock.audio = {"target_lufs": -14.0}
            spec_mock.cuts = []
            spec_mock.subtitles = []
            spec_mock.publish = {}
            qgate = QualityGate(spec_mock, tmp_dir)

            # Simulate Instagram promote throwing an error mid-flight
            orig_replace = os.replace
            def flaky_replace(src, dst):
                if ig_staging in src:
                    raise PermissionError("Simulated disk error during Instagram deployment!")
                return orig_replace(src, dst)

            with patch("os.replace", side_effect=flaky_replace):
                deployed = qgate._transactional_deploy(yt_staging, yt_dir, ig_staging, ig_dir)
                self.assertFalse(deployed, "Deployment must return False on exception")

            # CRITICAL ASSERTION: Since YouTube was promoted on a fresh day, rollback MUST remove yt_dir so no partial release remains!
            self.assertFalse(os.path.exists(yt_dir), "Newly created YouTube directory must be deleted on rollback to prevent partial state!")
            self.assertFalse(os.path.exists(ig_dir), "Instagram directory must not remain")

    def test_12_cached_asset_hash_collision_and_blacklist_rejection(self):
        """Verify that pre-existing cached files on disk are checked against registry hash and active reservations."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            reg_path = os.path.join(tmp_dir, "registry.json")
            reg = AssetRegistry(reg_path)

            # Setup a file that already exists on disk
            cached_file = os.path.join(tmp_dir, "scene1_pexels_cached123.mp4")
            with open(cached_file, "wb") as f:
                f.write(b"REPEATED_CONTENT_BYTES_999")

            # Register this hash as used in Day 2
            fhash = reg.compute_file_hash(cached_file)
            reg.register_asset("pexels", "cached123", "video", "test action", "test query", file_path=cached_file)
            reg.record_usage("pexels", "cached123", "Gun_2", 0.0, 5.0, file_path=cached_file)

            with patch("core.semantic_selector.registry", reg):
                selector = SemanticSelector()
                v_need = VisualNeed(
                    scene_id="scene1",
                    spoken_text="test text",
                    subject_action="test action",
                    environment="test env",
                    emotion="test emotion",
                    media_type="video",
                    avoid=[],
                    queries=["test query"],
                    required_duration=2.0
                )

                # Mock candidate matching the cached file
                mock_cand = {
                    "id": "cached123",
                    "provider": "pexels",
                    "duration": 5.0,
                    "width": 1080,
                    "height": 1920,
                    "tags": "test action test env",
                    "download_url": "http://example.com/cached.mp4"
                }

                with patch("core.semantic_selector.pexels_search_video", return_value=[mock_cand]), \
                     patch("core.semantic_selector.search_pixabay_videos", return_value=[]):
                    # Attempt selecting for Gun_2 where it was already used -> MUST REJECT cached file!
                    res_used = selector.select_asset(v_need, current_day="Gun_2", target_dir=tmp_dir)
                    self.assertEqual(res_used.get("fallback_action"), "speaker_cut", "Cached asset already used in current_day must be rejected")

                    # Attempt selecting when fhash is in active_reservations -> MUST REJECT
                    selector.active_reservations.add(fhash)
                    res_reserved = selector.select_asset(v_need, current_day="Gun_3", target_dir=tmp_dir)
                    self.assertEqual(res_reserved.get("fallback_action"), "speaker_cut", "Cached asset in active reservations must be rejected")

    def test_13_watermark_spec_validation_and_overlay_chain(self):
        """Verify watermark configuration validation in VideoSpec, default inheritance, and overlay filter inclusion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 0. Test default inheritance when watermark key is omitted
            spec_no_wm = {
                "meta": {"day": "Gun_Test"},
                "source": {"raw_video_path": "dummy.mp4", "in_point": 0.0, "out_point": 10.0},
                "audio": {},
                "cuts": [],
                "subtitles": []
            }
            spec_default = VideoSpec.from_dict(spec_no_wm)
            self.assertIsNotNone(spec_default.watermark)
            self.assertTrue(spec_default.watermark.get("enabled"))
            self.assertEqual(spec_default.watermark.get("x"), "W-w-40")
            self.assertEqual(spec_default.watermark.get("y"), "H-h-130")

            # 1. Validation test: missing image path
            spec_dict = {
                "meta": {"day": "Gun_Test"},
                "source": {"raw_video_path": "dummy.mp4", "in_point": 0.0, "out_point": 10.0},
                "audio": {},
                "cuts": [],
                "subtitles": [],
                "watermark": {
                    "enabled": True,
                    "image_path": os.path.join(tmp_dir, "non_existent_wm.png")
                }
            }
            spec = VideoSpec.from_dict(spec_dict)
            errors = spec.validate(allow_unresolved=True)
            self.assertTrue(any("Watermark image not found" in e for e in errors))

            # 2. Validation test: valid image
            wm_img_path = os.path.join(tmp_dir, "wm.png")
            with open(wm_img_path, "wb") as f:
                f.write(b"PNG_DUMMY_DATA")
            spec.watermark["image_path"] = wm_img_path
            raw_v_path = os.path.join(tmp_dir, "raw.mp4")
            with open(raw_v_path, "wb") as f:
                f.write(b"RAW_VIDEO_DATA")
            spec.source["raw_video_path"] = raw_v_path
            errors_valid = spec.validate(allow_unresolved=True)
            self.assertEqual(len(errors_valid), 0)

            # 3. TimelineCompiler overlay filter verification
            compiler = TimelineCompiler(spec, tmp_dir)
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                with patch.object(compiler, "collect_and_normalize_cuts", return_value=[]):
                    with patch("engine.timeline.SubtitleEngine.generate_all_badges", return_value=[]):
                        out_v = os.path.join(tmp_dir, "out_v.mp4")
                        compiler.compile_visual(out_v, force=True)

                        # Inspect the ffmpeg command that was called
                        call_args = mock_run.call_args[0][0]
                        cmd_str = " ".join(call_args)
                        self.assertIn("-i " + wm_img_path, cmd_str)
                        self.assertIn("overlay=W-w-40:H-h-130[v_watermark]", cmd_str)
                        self.assertIn("[v_watermark]fade=t=out", cmd_str)

if __name__ == "__main__":
    unittest.main()
