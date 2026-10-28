import time
import os
from pathlib import Path
from google import genai
from google.genai import types

def load_saved_api_key() -> str:
    """Membaca API key otomatis dari api_key.txt atau .env."""
    root_dir = Path(__file__).parent.parent
    txt_path = root_dir / "api_key.txt"
    if txt_path.exists():
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        return env_key.strip()

    return ""

def save_api_key(api_key: str) -> bool:
    """Menyimpan API Key secara permanen ke file api_key.txt di root direktori."""
    if not api_key or not api_key.strip():
        return False
    root_dir = Path(__file__).parent.parent
    txt_path = root_dir / "api_key.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(api_key.strip())
        return True
    except Exception:
        return False

def get_gemini_client(api_key: str = None) -> genai.Client:
    key = (api_key or load_saved_api_key()).strip()
    if not key:
        raise ValueError("API Key Gemini belum diisi. Masukkan API key di antarmuka atau di berkas api_key.txt.")
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20.0))

PREFERRED_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-3.8-flash"]

SUPPORTED_LANGUAGES = {
    "id": "Bahasa Indonesia",
    "en": "Bahasa Inggris (English)",
    "ar": "Bahasa Arab (العربية)",
    "zh": "Bahasa Mandarin (中文 / Hanzi)",
    "de": "Bahasa Jerman (Deutsch)",
    "es": "Bahasa Spanyol (Español)",
    "auto": "Deteksi Otomatis (Auto-Detect)"
}

def transcribe_with_gemini(
    audio_path: str,
    api_key: str = None,
    title: str = "Wawancara",
    language_code: str = "id",
    status_callback=None,
    *args,
    **kwargs
) -> str:
    """
    Mentranskripsikan berkas audio menggunakan Gemini File API (Google AI Studio - Free tier).
    Mendukung rekaman panjang hingga berjam-jam dan multibahasa secara verbatim.
    """
    client = get_gemini_client(api_key)
    lang_desc = SUPPORTED_LANGUAGES.get(language_code, "Bahasa Indonesia")

    if status_callback:
        status_callback("Mengunggah berkas audio ke Google Gemini...")

    upload_ref = client.files.upload(file=audio_path)

    if status_callback:
        status_callback("Memverifikasi berkas audio di cloud...")

    waited = 0
    while upload_ref.state.name == "PROCESSING":
        time.sleep(3)
        waited += 3
        if status_callback:
            status_callback(f"Menunggu verifikasi audio di cloud ({waited} detik)...")
        upload_ref = client.files.get(name=upload_ref.name)

    if upload_ref.state.name == "FAILED":
        raise RuntimeError("Berkas audio gagal diproses oleh server Gemini.")

    if status_callback:
        if language_code == "auto":
            status_callback("AI sedang mendeteksi bahasa dan menyusun transkrip verbatim...")
        else:
            status_callback(f"AI sedang menyusun transkrip verbatim dalam {lang_desc}...")

    if language_code == "auto":
        instruction_lang = (
            "ke dalam bahasa asli yang dituturkan oleh narasumber dalam rekaman "
            "(deteksi otomatis bahasa ucapan asli, pertahankan bahasa aslinya secara verbatim tanpa menerjemahkan ke bahasa lain)"
        )
    else:
        instruction_lang = (
            f"ke dalam {lang_desc} sesuai ucapan asli narasumber "
            f"(pertahankan bahasa aslinya secara verbatim, JANGAN menerjemahkan ke bahasa lain)"
        )

    prompt = (
        f"Judul Wawancara: {title}\n\n"
        f"Tolong transkripsikan rekaman wawancara audio ini {instruction_lang} secara akurat, utuh, mengalir, dan rapi.\n\n"
        "Panduan format transkripsi:\n"
        "1. Tuliskan hasil transkrip secara bersih dalam bentuk paragraf-paragraf dialog yang mengalir alami dan nyaman dibaca dalam BAHASA ASLINYA (Verbatim Original).\n"
        "2. JANGAN menerjemahkan ucapan ke bahasa lain (misal jika rekaman Arab tetap tulis dalam aksara Arab/Hijaiyah, Mandarin tetap dalam aksara Hanzi, Inggris dalam bahasa Inggris, Jerman dalam bahasa Jerman, Spanyol dalam bahasa Spanyol, Indonesia dalam Bahasa Indonesia).\n"
        "3. JANGAN sertakan penanda waktu atau timestamp sama sekali (jangan ada format [HH:MM:SS] atau penanda waktu lainnya).\n"
        "4. Tuliskan kalimat demi kalimat secara lengkap sesuai ucapan narasumber tanpa mengubah arti atau memotong perkataan asli.\n"
        "5. Jangan berikan kalimat pembuka, pengantar, atau penutup AI (misalnya 'Berikut adalah transkrip...'). Langsung mulai dari isi transkrip wawancara."
    )

    last_error = None
    transcript_text = None

    for model_name in PREFERRED_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[upload_ref, prompt]
            )
            if response and response.text:
                transcript_text = response.text.strip()
                break
        except Exception as exc:
            last_error = exc
            continue

    # Hapus file sementara dari cloud setelah selesai agar tidak memenuhi kuota penyimpanan
    try:
        client.files.delete(name=upload_ref.name)
    except Exception:
        pass

    if transcript_text is None:
        raise RuntimeError(f"Gagal mendapatkan respon dari model Gemini:\n{last_error}")

    return transcript_text

def refine_transcript_with_ai(
    transcript_text: str,
    api_key: str = None,
    language_code: str = "id",
    status_callback=None,
    *args,
    **kwargs
) -> str:
    """
    Menyempurnakan hasil transkrip menggunakan Gemini AI:
    - Memperbaiki salah dengar (typo model ASR) dan ejaan baku sesuai bahasa aslinya.
    - Merapikan tanda baca dan format dialog pembicara.
    - Menjaga integritas konten asli tanpa memotong atau mengarang.
    - Mendukung teks panjang berjam-jam melalui chunking terukur.
    """
    if not transcript_text or not transcript_text.strip():
        return transcript_text

    client = get_gemini_client(api_key)
    lang_desc = SUPPORTED_LANGUAGES.get(language_code, "Bahasa Indonesia")

    if language_code == "auto":
        target_info = "bahasa asli teks tersebut (pertahankan bahasa aslinya secara verbatim, JANGAN diterjemahkan ke bahasa lain)"
    else:
        target_info = f"{lang_desc} (pertahankan tetap dalam {lang_desc}, JANGAN diterjemahkan ke bahasa lain)"

    # Bagi teks per baris untuk membatasi ukuran per request (~200 baris per bagian)
    lines = transcript_text.splitlines()
    chunk_size = 200
    chunks = []
    
    current_chunk = []
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= chunk_size:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    refined_parts = []
    total_chunks = len(chunks)

    prompt_instruction = (
        "Kamu adalah editor bahasa dan transkrip profesional. Tugasmu adalah menyempurnakan dan mengoreksi "
        f"hasil transkrip wawancara dalam {target_info} berikut.\n\n"
        "Panduan koreksi:\n"
        "1. Perbaiki salah dengar (ASR misheard), kata typo, dan ejaan kata baku sesuai kaidah bahasa aslinya (misalnya EYD untuk Bahasa Indonesia, grammar baku untuk Inggris/Jerman/Spanyol, tata bahasa Arab/Mandarin yang benar).\n"
        "2. Rapikan tanda baca, huruf kapital, dan jeda antarparagraf percakapan agar enak dibaca seperti dokumen transkrip resmi.\n"
        "3. Pertahankan bahasa aslinya secara verbatim (JANGAN diterjemahkan ke bahasa lain).\n"
        "4. JANGAN sertakan penanda waktu atau timestamp [HH:MM:SS]. Jika pada teks masukan ada penanda waktu, hilangkan penanda tersebut sehingga teks bersih.\n"
        "5. JANGAN menambah karangan baru atau memotong isi percakapan penting (tetap setia pada perkataan asli narasumber).\n"
        "6. Langsung berikan teks transkrip hasil perbaikan tanpa ada kalimat pengantar atau penutup dari AI.\n\n"
        "Teks yang perlu disempurnakan:\n"
    )

    for idx, chunk in enumerate(chunks, 1):
        if status_callback:
            status_callback(f"Menyempurnakan ejaan dan tanda baca (Bagian {idx} dari {total_chunks})...")

        full_prompt = prompt_instruction + chunk

        chunk_result = None
        last_error = None
        for model_name in PREFERRED_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                if response and response.text:
                    chunk_result = response.text.strip()
                    break
            except Exception as exc:
                last_error = exc
                continue

        if chunk_result is None:
            # Fallback jika error: gunakan teks asli untuk chunk tersebut
            refined_parts.append(chunk)
        else:
            refined_parts.append(chunk_result)

    return "\n\n".join(refined_parts)
