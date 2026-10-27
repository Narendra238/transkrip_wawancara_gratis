import os
import av
from faster_whisper import WhisperModel

# Penanganan kompatibilitas PyAV:
# Versi PyAV 19+ menghapus argumen 'metadata_errors', sedangkan faster-whisper masih mengirimkannya.
# Monkeypatch ini memastikan pemanggilan av.open selalu aman di versi PyAV mana pun.
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

def transcribe_audio(audio_path: str, model_size: str = "base", language: str = "id", progress_callback=None):
    """
    Transkripsi audio secara lokal offline menggunakan faster-whisper.
    """
    device = "cpu"
    compute_type = "int8"
    
    # Inisialisasi model lokal
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    segments_iter, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        word_timestamps=False
    )
    
    segments = []
    for segment in segments_iter:
        segments.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip()
        })
        if progress_callback:
            progress_callback(min(0.95, len(segments) / (len(segments) + 20)))
            
    return {"segments": segments, "language": getattr(info, "language", None)}
