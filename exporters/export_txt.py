import os

def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def build_txt_from_segments(segments, include_timestamps: bool = False) -> str:
    """
    Mengubah daftar segmen menjadi teks transkrip.
    Jika include_timestamps=False (default), menghasilkan paragraf dialog bersih mengalir
    persis seperti format dokumen TurboScribe tanpa penanda [HH:MM:SS].
    """
    if include_timestamps:
        lines = []
        for seg in segments:
            text = seg["text"].strip()
            if text:
                lines.append(f"[{format_timestamp(seg['start'])}] {text}")
        return "\n".join(lines)

    paragraphs = []
    current_para = []
    last_end = 0.0

    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        start = seg.get("start", 0.0)
        # Buat paragraf baru jika ada jeda hening percakapan (> 1.8 detik) atau panjang paragraf mencukupi
        if current_para and (start - last_end > 1.8 or len(" ".join(current_para)) > 260):
            paragraphs.append(" ".join(current_para))
            current_para = [text]
        else:
            current_para.append(text)
        last_end = seg.get("end", start)

    if current_para:
        paragraphs.append(" ".join(current_para))

    return "\n\n".join(paragraphs)

def save_txt(text: str, save_path: str = None) -> bytes:
    """Menyimpan teks ke berkas .txt dan mengembalikan bytes berkas."""
    content_bytes = text.encode("utf-8")
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content_bytes)
    return content_bytes
