import os

def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def build_txt_from_segments(segments, include_timestamps: bool = True) -> str:
    lines = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        if include_timestamps:
            lines.append(f"[{format_timestamp(seg['start'])}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)

def save_txt(text: str, save_path: str = None) -> bytes:
    """Menyimpan teks ke berkas .txt dan mengembalikan bytes berkas."""
    content_bytes = text.encode("utf-8")
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content_bytes)
    return content_bytes
