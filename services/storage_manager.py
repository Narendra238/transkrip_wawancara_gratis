import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

def sanitize_folder_name(name: str) -> str:
    """Membersihkan karakter ilegal pada nama folder dan berkas Windows."""
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
    """Membuka folder hasil transkrip di Windows File Explorer."""
    if os.path.exists(folder_path):
        try:
            os.startfile(folder_path)
        except Exception:
            subprocess.Popen(["explorer", os.path.normpath(folder_path)])
