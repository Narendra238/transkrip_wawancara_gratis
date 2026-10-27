import os
import shutil
import subprocess
from pathlib import Path
import imageio_ffmpeg

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".mpeg", ".mpg", ".avi", ".ts"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}

def get_ffmpeg_binary() -> str:
    """Mencari executable FFmpeg di PATH sistem atau dari imageio-ffmpeg bawaan."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.exists(bundled):
            return bundled
    except Exception:
        pass
    return "ffmpeg"

def extract_and_compress_audio(source_path: str, output_dir: str, target_format: str = "mp3") -> str:
    """
    Mengekstrak dan mengompres audio dari berkas video atau audio besar.
    Untuk video 3 jam, kompresi ke MP3 mono 16kHz 64kbps menghasilkan berkas ~40-60 MB
    sehingga sangat ringan, cepat diproses, dan hemat memori/kuota.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    stem = Path(source_path).stem
    output_filename = f"{stem}_audio.{target_format}"
    output_path = os.path.join(output_dir, output_filename)

    if target_format == "wav":
        command = [
            ffmpeg_exe, "-y", "-i", source_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", output_path
        ]
    else:
        # Default MP3 mono 16kHz 64kbps - sangat efisien untuk rekaman wawancara panjang
        command = [
            ffmpeg_exe, "-y", "-i", source_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-b:a", "64k", output_path
        ]

    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Executable FFmpeg tidak ditemukan. Pastikan paket imageio-ffmpeg telah terpasang di venv."
        ) from exc

    if completed.returncode != 0 or not os.path.exists(output_path):
        detail = (completed.stderr or completed.stdout or "Tidak ada pesan detail dari proses")[-2000:]
        raise RuntimeError(f"Gagal memproses audio:\n{detail}")

    return output_path

def prepare_audio(source_path: str, output_dir: str, for_gemini: bool = True) -> str:
    """
    Menyiapkan berkas audio untuk proses transkripsi.
    - Jika input video (.mp4 dll), wajib diekstrak audionya terlebih dahulu.
    - Jika input audio (.mp3 dll), jika ukurannya sangat besar (> 50MB) dikompres agar hemat memori.
    """
    ext = Path(source_path).suffix.lower()
    file_size_mb = os.path.getsize(source_path) / (1024 * 1024)

    # Jika file adalah video, ekstrak audionya
    if ext in VIDEO_EXTENSIONS:
        fmt = "mp3" if for_gemini else "wav"
        return extract_and_compress_audio(source_path, output_dir, target_format=fmt)

    # Jika file sudah berupa mp3/wav/m4a tetapi sangat besar (> 100MB), kompres agar ringan
    if file_size_mb > 100 and ext != ".mp3":
        return extract_and_compress_audio(source_path, output_dir, target_format="mp3")

    return source_path
