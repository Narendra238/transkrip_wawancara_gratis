import time
import os
from google import genai
from google.genai import types

def transcribe_with_gemini(
    audio_path: str,
    api_key: str,
    title: str = "Wawancara",
    status_callback=None
) -> str:
    """
    Mentranskripsikan berkas audio menggunakan Gemini API (Google AI Studio - Free tier).
    Mendukung rekaman panjang hingga berjam-jam dengan File API.
    """
    if not api_key or not api_key.strip():
        raise ValueError("API Key Gemini belum diisi. Masukkan API key dari Google AI Studio.")

    client = genai.Client(api_key=api_key.strip())

    if status_callback:
        status_callback("Mengunggah berkas audio ke Google Gemini...")

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    upload_ref = client.files.upload(file=audio_path)

    # Menunggu proses pemrosesan file di cloud jika diperlukan
    if status_callback:
        status_callback("Memverifikasi berkas audio...")

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
        status_callback("AI sedang menyusun transkrip wawancara ke Bahasa Indonesia...")

    prompt = (
        f"Judul Wawancara: {title}\n\n"
        "Tolong transkripsikan rekaman wawancara audio ini ke dalam Bahasa Indonesia secara akurat, utuh, dan rapi.\n\n"
        "Panduan format:\n"
        "1. Pisahkan setiap dialog berdasarkan pembicara (misalnya 'Pewawancara:', 'Narasumber:', atau 'Pembicara 1:', 'Pembicara 2:').\n"
        "2. Sertakan penanda waktu / timestamp dalam format [HH:MM:SS] pada setiap awal percakapan atau pergantian topik.\n"
        "3. Tuliskan teks dalam Bahasa Indonesia yang baik dan mudah dibaca tanpa mengubah inti perkataan narasumber.\n"
        "4. Jangan berikan kalimat pembuka atau penutup AI (misalnya 'Berikut adalah transkrip...'). Langsung mulai dari isi transkrip."
    )

    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]
    last_error = None
    transcript_text = None

    for model_name in models_to_try:
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

    # Hapus file sementara dari cloud setelah selesai agar tidak memenuhi penyimpanan
    try:
        client.files.delete(name=upload_ref.name)
    except Exception:
        pass

    if transcript_text is None:
        raise RuntimeError(f"Gagal mendapatkan respon dari model Gemini:\n{last_error}")

    return transcript_text
