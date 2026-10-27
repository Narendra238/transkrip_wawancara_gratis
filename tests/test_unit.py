import os
import sys
import tempfile
import unittest
from pathlib import Path

# Tambahkan root proyek ke sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.storage_manager import sanitize_folder_name, create_output_directory
from services.media_processor import VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, get_ffmpeg_binary
from services.gemini_transcriber import SUPPORTED_LANGUAGES, load_saved_api_key
from services.transcriber import format_hms, is_cuda_available, _safe_av_open
from services.sus_manager import calculate_sus_score, SUS_QUESTIONS
from exporters.export_txt import format_timestamp, build_txt_from_segments, save_txt
from exporters.export_docx import build_docx

class TestStorageManager(unittest.TestCase):
    """Pengujian Unit untuk services/storage_manager.py"""

    def test_sanitize_folder_name_illegal_chars(self):
        dirty_name = 'Wawancara: "Narasumber" / Peneliti * A? <1> | 2'
        cleaned = sanitize_folder_name(dirty_name)
        for char in r'[\\/*?:"<>|]':
            self.assertNotIn(char, cleaned)
        self.assertNotIn(" ", cleaned)

    def test_sanitize_folder_name_empty_fallback(self):
        cleaned = sanitize_folder_name("   :::???***   ")
        self.assertEqual(cleaned, "Wawancara")

    def test_create_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = create_output_directory("Wawancara Uji Coba", base_dir=tmp_dir)
            self.assertTrue(os.path.exists(out_path))
            self.assertIn("Wawancara_Uji_Coba", out_path)
            self.assertIn("transkrip", out_path)

class TestExportTxt(unittest.TestCase):
    """Pengujian Unit untuk exporters/export_txt.py"""

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(0), "00:00:00")
        self.assertEqual(format_timestamp(65), "00:01:05")
        self.assertEqual(format_timestamp(3665), "01:01:05")

    def test_build_txt_with_timestamps(self):
        segments = [
            {"start": 0.0, "end": 2.5, "text": "Halo selamat pagi."},
            {"start": 3.0, "end": 5.0, "text": "Pagi juga."}
        ]
        result = build_txt_from_segments(segments, include_timestamps=True)
        self.assertIn("[00:00:00] Halo selamat pagi.", result)
        self.assertIn("[00:00:03] Pagi juga.", result)

    def test_build_txt_flowing_paragraphs(self):
        segments = [
            {"start": 0.0, "end": 1.0, "text": "Kalimat pertama."},
            {"start": 1.2, "end": 2.0, "text": "Kalimat kedua."}
        ]
        result = build_txt_from_segments(segments, include_timestamps=False)
        self.assertNotIn("[00:", result)
        self.assertIn("Kalimat pertama. Kalimat kedua.", result)

    def test_save_txt_utf8_multilingual(self):
        sample_multilingual = (
            "Bahasa Indonesia: Selamat datang\n"
            "English: Welcome\n"
            "Arabic: مرحبا بالعالم\n"
            "Chinese: 你好，世界\n"
            "German: Guten Tag mit Umlaut äöüß\n"
            "Spanish: Hola señor niño"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_file = os.path.join(tmp_dir, "test_utf8.txt")
            saved_bytes = save_txt(sample_multilingual, save_path=target_file)
            self.assertTrue(os.path.exists(target_file))
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, sample_multilingual)

class TestExportDocx(unittest.TestCase):
    """Pengujian Unit untuk exporters/export_docx.py"""

    def test_build_docx_output_bytes(self):
        text = "Ini adalah paragraf transkrip percobaan.\nParagraf kedua mengalir rapi."
        docx_bytes = build_docx(text, title="Wawancara Riset", language_label="Bahasa Indonesia")
        self.assertIsInstance(docx_bytes, bytes)
        self.assertGreater(len(docx_bytes), 1000)

    def test_build_docx_kwargs_tolerance(self):
        # Memastikan build_docx tidak crash jika menerima argumen tak terduga (kwargs)
        text = "Uji toleransi kwargs."
        docx_bytes = build_docx(
            text,
            title="Judul Uji",
            language_label="English",
            unexpected_param=123,
            extra_flag=True
        )
        self.assertIsInstance(docx_bytes, bytes)

    def test_build_docx_multilingual_save_disk(self):
        sample_multilingual = "مرحبا بالعالم\n你好世界\nHola mundo\nHallo Welt"
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_docx = os.path.join(tmp_dir, "test_doc.docx")
            docx_bytes = build_docx(sample_multilingual, title="Riset Arab & Mandarin", language_label="Multibahasa", save_path=target_docx)
            self.assertTrue(os.path.exists(target_docx))
            self.assertGreater(os.path.getsize(target_docx), 1000)

class TestTranscriberUtils(unittest.TestCase):
    """Pengujian Unit untuk services/transcriber.py"""

    def test_format_hms(self):
        self.assertEqual(format_hms(0), "00:00:00")
        self.assertEqual(format_hms(59), "00:00:59")
        self.assertEqual(format_hms(3600), "01:00:00")

    def test_is_cuda_available_returns_bool(self):
        cuda_status = is_cuda_available()
        self.assertIsInstance(cuda_status, bool)

    def test_pyav_safe_open_callable(self):
        # Memverifikasi bahwa _safe_av_open terdefinisi dan aman dipanggil
        self.assertTrue(callable(_safe_av_open))

class TestGeminiTranscriberConstants(unittest.TestCase):
    """Pengujian Unit untuk konfigurasi multibahasa gemini_transcriber.py"""

    def test_supported_languages_coverage(self):
        required_keys = ["id", "en", "ar", "zh", "de", "es", "auto"]
        for key in required_keys:
            self.assertIn(key, SUPPORTED_LANGUAGES)

    def test_load_saved_api_key_callable(self):
        key = load_saved_api_key()
        self.assertIsInstance(key, str)

class TestSUSCalculation(unittest.TestCase):
    """Pengujian Unit untuk kalkulasi System Usability Scale (SUS)"""

    def test_perfect_sus_score(self):
        # Jawaban sempurna: ganjil=5 (sangat setuju), genap=1 (sangat tidak setuju)
        perfect_responses = [5, 1, 5, 1, 5, 1, 5, 1, 5, 1]
        calc = calculate_sus_score(perfect_responses)
        self.assertEqual(calc["score"], 100.0)
        self.assertEqual(calc["grade"], "A")
        self.assertIn("Excellent", calc["adjective"])
        self.assertIn("Acceptable", calc["acceptability"])

    def test_worst_sus_score(self):
        # Jawaban terburuk: ganjil=1, genap=5
        worst_responses = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        calc = calculate_sus_score(worst_responses)
        self.assertEqual(calc["score"], 0.0)
        self.assertEqual(calc["grade"], "F")
        self.assertIn("Poor", calc["adjective"])
        self.assertIn("Not Acceptable", calc["acceptability"])

    def test_average_neutral_sus_score(self):
        # Jawaban netral semua bernilai 3
        neutral_responses = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        calc = calculate_sus_score(neutral_responses)
        self.assertEqual(calc["score"], 50.0)

    def test_invalid_sus_responses_length(self):
        with self.assertRaises(ValueError):
            calculate_sus_score([4, 2, 5])

    def test_invalid_sus_responses_range(self):
        with self.assertRaises(ValueError):
            calculate_sus_score([6, 1, 4, 2, 5, 1, 4, 2, 5, 1])

if __name__ == "__main__":
    unittest.main()
