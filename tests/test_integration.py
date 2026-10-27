import os
import sys
import wave
import struct
import math
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.media_processor import prepare_audio
from services.transcriber import transcribe_audio, is_cuda_available
from services.storage_manager import create_output_directory, sanitize_folder_name
from exporters.export_docx import build_docx
from exporters.export_txt import build_txt_from_segments, save_txt

def generate_tone_wav(file_path: str, duration_sec: float = 2.0, freq: float = 440.0, sample_rate: int = 16000):
    """
    Membuat file audio WAV 16kHz mono dengan gelombang sinus murni (nada 440 Hz)
    untuk pengujian integrasi utuh tanpa butuh internet atau file audio eksternal.
    """
    n_samples = int(duration_sec * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)      # Mono
        wf.setsampwidth(2)     # 16-bit PCM
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # Gelombang sinus
            sample = int(32767.0 * 0.25 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            frames.extend(struct.pack("<h", sample))
        wf.writeframes(frames)

class TestIntegrationPipeline(unittest.TestCase):
    """Pengujian Integrasi End-to-End Komponen Transkripsi Lokal"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_integration_")
        self.audio_path = os.path.join(self.test_dir, "audio_tone_test.wav")
        generate_tone_wav(self.audio_path, duration_sec=2.0)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_local_transcription_pipeline(self):
        """
        Menguji integrasi menyeluruh:
        1. Penyiapan audio (prepare_audio)
        2. Transkripsi dengan model faster-whisper (model tiny)
        3. Pembuatan folder otomatis (create_output_directory)
        4. Pembuatan berkas .docx dan .txt
        5. Verifikasi integritas berkas di disk
        """
        title = "Uji Integrasi Otomatis Pipeline"
        
        # 1. Penyiapan audio
        prepared_audio = prepare_audio(self.audio_path, self.test_dir, for_gemini=False)
        self.assertTrue(os.path.exists(prepared_audio))

        # 2. Transkripsi lokal dengan model 'tiny' (cepat dan ringan)
        # Gunakan cuda jika tersedia, fallback ke cpu
        hardware = "cuda" if is_cuda_available() else "cpu"
        
        progress_events = []
        def on_progress(fraction, msg):
            progress_events.append((fraction, msg))

        result = transcribe_audio(
            audio_path=prepared_audio,
            model_size="tiny",
            language="id",
            device=hardware,
            progress_callback=on_progress
        )

        # Verifikasi struktur hasil transkripsi
        self.assertIn("segments", result)
        self.assertIn("duration", result)
        self.assertIn("device_used", result)
        self.assertIsInstance(result["segments"], list)
        self.assertGreaterEqual(result["duration"], 1.5)

        # 3. Format teks dan dokumen
        transcript_text = build_txt_from_segments(result["segments"])
        if not transcript_text:
            transcript_text = "[Nada audio sintetis pengujian integrasi]"

        # 4. Penyimpanan ke folder output
        output_dir = create_output_directory(title, base_dir=self.test_dir)
        safe_title = sanitize_folder_name(title)
        
        docx_path = os.path.join(output_dir, f"{safe_title}.docx")
        txt_path = os.path.join(output_dir, f"{safe_title}.txt")

        docx_bytes = build_docx(transcript_text, title=title, language_label="Bahasa Indonesia", save_path=docx_path)
        txt_bytes = save_txt(transcript_text, save_path=txt_path)

        # 5. Verifikasi fisik berkas
        self.assertTrue(os.path.exists(docx_path), "Berkas DOCX harus berhasil ditulis ke disk.")
        self.assertTrue(os.path.exists(txt_path), "Berkas TXT harus berhasil ditulis ke disk.")
        self.assertGreater(os.path.getsize(docx_path), 500, "Ukuran berkas DOCX harus valid.")
        self.assertGreater(os.path.getsize(txt_path), 0, "Ukuran berkas TXT harus valid.")

if __name__ == "__main__":
    unittest.main()
