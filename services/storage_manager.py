import os
import re
import platform
import subprocess
from datetime import datetime
from pathlib import Path

def sanitize_folder_name(name: str) -> str:
    """Membersihkan karakter ilegal pada nama folder dan berkas (Windows/Linux/macOS)."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    cleaned = re.sub(r'\s+', "_", cleaned)
    return cleaned or "Wawancara"

def create_output_directory(title: str, base_dir: str = None) -> str:
    """
    Membuat folder keluaran dengan format:
    transkrip/HHMM_DDMMYYYY_JudulWawancara
    Contoh: transkrip/0753_27102026_Wawancara_NarasumberA
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    safe_title = sanitize_folder_name(title)
    timestamp_prefix = datetime.now().strftime("%H%M_%d%m%Y")
    folder_name = f"{timestamp_prefix}_{safe_title}"

    target_path = os.path.join(base_dir, "transkrip", folder_name)
    os.makedirs(target_path, exist_ok=True)
    return target_path

def open_folder_in_explorer(folder_path: str):
    """Membuka folder hasil transkrip di File Explorer sesuai sistem operasi (Windows/macOS/Linux)."""
    if not os.path.exists(folder_path):
        return

    cur_os = platform.system()
    try:
        if cur_os == "Windows":
            try:
                os.startfile(folder_path)
            except Exception:
                subprocess.Popen(["explorer", os.path.normpath(folder_path)])
        elif cur_os == "Darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])
    except Exception:
        pass
