import os
import av
import ctranslate2
from faster_whisper import WhisperModel

# Penanganan kompatibilitas PyAV
_orig_av_open = av.open
def _safe_av_open(*args, **kwargs):
    try:
        return _orig_av_open(*args, **kwargs)
    except TypeError as e:
        if "metadata_errors" in str(e):
            kwargs.pop("metadata_errors", None)
            return _orig_av_open(*args, **kwargs)
        raise

av.open = _safe_av_open

def is_cuda_available() -> bool:
    """Mengecek apakah kartu grafis NVIDIA dan runtime CUDA terdeteksi."""
    try:
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False

def format_hms(seconds: float) -> str:
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: str = "id",
    device: str = "auto",
    progress_callback=None,
    *args,
    **kwargs
):
    """
    Transkripsi audio lokal menggunakan faster-whisper.
    Jika GPU dipilih namun file runtime CUDA (cublas64_12.dll) belum ada di Windows,
    sistem akan secara otomatis dan aman beralih ke CPU tanpa memunculkan galat crash.
    """
    selected_device = "cpu"
    compute_type = "int8"

    if device == "cuda" or (device == "auto" and is_cuda_available()):
        selected_device = "cuda"
        compute_type = "float16"
    else:
        selected_device = "cpu"
        compute_type = "int8"

    def run_whisper(dev, ctype):
        whisper_lang = None if (language in ("auto", "", None) or not language) else language
        model = WhisperModel(model_size, device=dev, compute_type=ctype)
        segments_iter, info = model.transcribe(
            audio_path,
            language=whisper_lang,
            beam_size=5,
            vad_filter=True,
            word_timestamps=False
        )
        total_duration = getattr(info, "duration", 0.0) or 0.0
        segments = []

        for segment in segments_iter:
            seg_data = {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip()
            }
            segments.append(seg_data)

            if progress_callback:
                if total_duration > 0:
                    fraction = min(0.99, seg_data["end"] / total_duration)
                    cur_str = format_hms(seg_data["end"])
                    tot_str = format_hms(total_duration)
                    progress_callback(fraction, f"{int(fraction * 100)}% ({cur_str} / {tot_str})")
                else:
                    progress_callback(min(0.95, len(segments) / (len(segments) + 30)), f"{len(segments)} segmen")

        return {
            "segments": segments,
            "language": getattr(info, "language", None),
            "duration": total_duration,
            "device_used": dev
        }

    try:
        return run_whisper(selected_device, compute_type)
    except Exception as exc:
        err_msg = str(exc).lower()
        if selected_device == "cuda" and ("cublas" in err_msg or "cuda" in err_msg or "not found" in err_msg):
            # Fallback otomatis ke CPU
            if progress_callback:
                progress_callback(0.01, "Pustaka CUDA cublas belum terpasang di Windows, beralih otomatis ke CPU...")
            return run_whisper("cpu", "int8")
        else:
            raise exc
