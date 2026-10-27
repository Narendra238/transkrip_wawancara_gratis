import os
import sys
import wave
import struct
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.media_processor import prepare_audio, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from services.storage_manager import create_output_directory, sanitize_folder_name
from services.sus_manager import save_sus_evaluation, load_sus_statistics, SUS_QUESTIONS
from exporters.export_txt import build_txt_from_segments, save_txt
from exporters.export_docx import build_docx

def generate_synthetic_wav(file_path: str, duration_sec: float = 1.0, sample_rate: int = 16000):
    """Membuat berkas audio WAV sintetis mono 16kHz untuk pengujian tanpa memerlukan file eksternal."""
    n_samples = int(duration_sec * sample_rate)
    with wave.open(file_path, "wb") as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(sample_rate)
        # Tulis data hening (silent frames)
        raw_data = struct.pack("<" + "h" * n_samples, *([0] * n_samples))
        wav_file.writeframes(raw_data)

class TestFunctionalWorkflows(unittest.TestCase):
    """Pengujian Fungsional untuk Fitur-Fitur Utama Aplikasi"""

    def test_functional_media_extensions_coverage(self):
        """Memverifikasi seluruh format video dan audio umum terdaftar di sistem."""
        common_videos = [".mp4", ".mov", ".mkv", ".webm"]
        common_audios = [".mp3", ".wav", ".m4a", ".aac"]
        for ext in common_videos:
            self.assertIn(ext, VIDEO_EXTENSIONS, f"Ekstensi video {ext} harus didukung.")
        for ext in common_audios:
            self.assertIn(ext, AUDIO_EXTENSIONS, f"Ekstensi audio {ext} harus didukung.")

    def test_functional_prepare_audio_passthrough(self):
        """Memverifikasi prepare_audio pada file audio WAV sintetis berukuran wajar."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_wav = os.path.join(tmp_dir, "sample_interview.wav")
            generate_synthetic_wav(sample_wav, duration_sec=1.5)
            self.assertTrue(os.path.exists(sample_wav))

            # prepare_audio seharusnya mengembalikan file langsung jika sudah berupa WAV/MP3 kecil
            prepared = prepare_audio(sample_wav, tmp_dir, for_gemini=False)
            self.assertTrue(os.path.exists(prepared))
            self.assertEqual(prepared, sample_wav)

    def test_functional_transcript_to_documents_pipeline(self):
        """
        Menguji alur fungsional pengolahan segmen ASR menjadi dokumen TXT dan DOCX
        lengkap dengan judul wawancara, penamaan folder, dan metadata.
        """
        sample_segments = [
            {"start": 0.0, "end": 3.2, "text": "Selamat pagi rekan-rekan peneliti."},
            {"start": 3.5, "end": 6.8, "text": "Hari ini kita membahas evaluasi model transkripsi."},
            {"start": 7.0, "end": 10.5, "text": "Hasil performa pada GPU RTX 4060 menunjukkan efisiensi tinggi."}
        ]

        title = "Wawancara Evaluasi Tim Peneliti"
        with tempfile.TemporaryDirectory() as tmp_base:
            output_dir = create_output_directory(title, base_dir=tmp_base)
            safe_name = sanitize_folder_name(title)

            # 1. Format teks mengalir tanpa timestamp
            txt_content = build_txt_from_segments(sample_segments, include_timestamps=False)
            txt_target = os.path.join(output_dir, f"{safe_name}.txt")
            txt_bytes = save_txt(txt_content, save_path=txt_target)
            self.assertTrue(os.path.exists(txt_target))
            self.assertGreater(len(txt_bytes), 0)

            # 2. Format Word DOCX
            docx_target = os.path.join(output_dir, f"{safe_name}.docx")
            docx_bytes = build_docx(txt_content, title=title, language_label="Bahasa Indonesia", save_path=docx_target)
            self.assertTrue(os.path.exists(docx_target))
            self.assertGreater(len(docx_bytes), 1000)

            # 3. Format teks dengan penanda waktu [HH:MM:SS]
            txt_ts_content = build_txt_from_segments(sample_segments, include_timestamps=True)
            self.assertIn("[00:00:00]", txt_ts_content)
            self.assertIn("[00:00:03]", txt_ts_content)

    def test_functional_multilingual_export_pipeline(self):
        """Menguji fungsionalitas pemrosesan teks multibahasa (Arab, Hanzi, Jerman, Spanyol)."""
        multilingual_segments = [
            {"start": 0.0, "end": 2.0, "text": "مرحبا بكم في هذا اللقاء"},
            {"start": 2.5, "end": 4.5, "text": "欢迎参加这次访谈"},
            {"start": 5.0, "end": 7.0, "text": "Herzlich willkommen zum Interview mit präziser Sprache"},
            {"start": 7.5, "end": 9.5, "text": "Bienvenidos a la entrevista formal en español"}
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            full_text = build_txt_from_segments(multilingual_segments)
            docx_path = os.path.join(tmp_dir, "multilingual_test.docx")
            txt_path = os.path.join(tmp_dir, "multilingual_test.txt")

            save_txt(full_text, save_path=txt_path)
            build_docx(full_text, title="Wawancara Multibahasa", language_label="Deteksi Otomatis", save_path=docx_path)

            self.assertTrue(os.path.exists(docx_path))
            self.assertTrue(os.path.exists(txt_path))

            with open(txt_path, "r", encoding="utf-8") as f:
                saved_text = f.read()
            self.assertIn("مرحبا بكم", saved_text)
            self.assertIn("欢迎参加", saved_text)
            self.assertIn("präziser", saved_text)
            self.assertIn("español", saved_text)

    def test_functional_sus_lifecycle(self):
        """Menguji fungsionalitas pengisian kuesioner SUS dari input hingga penyimpanan dan agregasi."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Simpan responden pertama (Skor Tinggi: 85.0)
            res1 = [5, 2, 4, 1, 5, 2, 5, 1, 4, 1]
            out1 = save_sus_evaluation(
                respondent_name="Dr. Budi",
                role="Dosen Peneliti",
                responses=res1,
                feedback="Sangat cepat dengan GPU RTX 4060.",
                base_dir=tmp_dir
            )
            self.assertGreaterEqual(out1["calculation"]["score"], 80.0)
            self.assertEqual(out1["total_records"], 1)

            # 2. Simpan responden kedua (Skor Sedang: 72.5)
            res2 = [4, 2, 4, 2, 4, 2, 4, 2, 4, 3]
            out2 = save_sus_evaluation(
                respondent_name="Siti Rahma",
                role="Mahasiswa Riset",
                responses=res2,
                feedback="Tampilan bersih dan mudah digunakan.",
                base_dir=tmp_dir
            )
            self.assertEqual(out2["total_records"], 2)

            # 3. Muat dan uji statistik agregasi
            stats = load_sus_statistics(base_dir=tmp_dir)
            self.assertEqual(stats["total_respondents"], 2)
            self.assertGreater(stats["average_score"], 70.0)
            self.assertEqual(len(stats["records"]), 2)

if __name__ == "__main__":
    unittest.main()
