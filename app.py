import os
import tempfile
from pathlib import Path
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Muat environment variable (.env) jika ada
load_dotenv()

from services.media_processor import prepare_audio, get_ffmpeg_binary
from services.gemini_transcriber import transcribe_with_gemini
from services.transcriber import transcribe_audio
from services.storage_manager import create_output_directory, sanitize_folder_name, open_folder_in_explorer
from exporters.export_docx import build_docx
from exporters.export_txt import build_txt_from_segments, save_txt

# Konfigurasi Halaman - Bersih, formal, tanpa simbol/emoji
st.set_page_config(
    page_title="Transkrip Wawancara",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan minimalis profesional tanpa ornamen berlebihan
st.markdown("""
<style>
    /* Tipografi dan tata letak */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .main-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .main-desc {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .info-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.85rem 1rem;
        margin-bottom: 1.25rem;
        font-size: 0.9rem;
        color: #334155;
    }
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 6px;
        padding: 0.85rem 1rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        font-size: 0.92rem;
        color: #166534;
    }
    /* Tombol standar */
    .stButton>button {
        border-radius: 4px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Header Halaman
st.markdown('<div class="main-title">Transkrip Wawancara</div>', unsafe_allow_html=True)
st.markdown('<div class="main-desc">Aplikasi pengubah rekaman wawancara (audio dan video) menjadi teks Bahasa Indonesia dalam format DOCX dan TXT.</div>', unsafe_allow_html=True)

# Panel Samping (Pengaturan)
with st.sidebar:
    st.subheader("Pengaturan Transkripsi")
    
    engine_choice = st.radio(
        "Metode Transkripsi",
        [
            "Google Gemini (Online - Disarankan untuk durasi panjang)",
            "Whisper Lokal (Offline - Berjalan di komputer)"
        ],
        index=0,
        help="Google Gemini mampu memproses rekaman berdurasi 3 jam dalam 1-2 menit secara gratis. Whisper Lokal berjalan di CPU tanpa internet."
    )
    
    saved_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key = ""
    
    if "Gemini" in engine_choice:
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("api_key", saved_api_key),
            type="password",
            help="Dapatkan API key gratis di Google AI Studio (aistudio.google.com/app/apikey)."
        )
        if gemini_api_key:
            st.session_state["api_key"] = gemini_api_key
            if st.button("Simpan API Key untuk sesi berikutnya"):
                env_path = Path(__file__).parent / ".env"
                with open(env_path, "w", encoding="utf-8") as env_f:
                    env_f.write(f"GEMINI_API_KEY={gemini_api_key.strip()}\n")
                st.success("API Key berhasil disimpan di komputer lokal.")
        else:
            st.info("Kunci API Gemini diperlukan untuk metode online. Kunci ini gratis dari Google AI Studio.")
    else:
        model_size = st.selectbox(
            "Ukuran Model Whisper",
            ["tiny", "base", "small", "medium"],
            index=1,
            help="Pilih 'base' untuk keseimbangan kecepatan. Untuk video 3 jam di CPU, proses lokal memerlukan waktu lebih lama."
        )

    st.markdown("---")
    st.markdown(
        "<small style='color: #64748b;'>"
        "Penyimpanan otomatis:<br>"
        "Hasil tersimpan di folder <code>transkrip/HHMM_DDMMYYYY_Judul/</code>"
        "</small>",
        unsafe_allow_html=True
    )

# Area Formulir Utama
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.subheader("1. Identitas Rekaman")
    interview_title = st.text_input(
        "Nama atau Judul Wawancara",
        placeholder="Contoh: Wawancara Narasumber A - Evaluasi Program",
        help="Judul ini akan digunakan sebagai penamaan folder hasil dan judul dokumen."
    )

with col_right:
    st.subheader("2. Sumber Berkas")
    input_mode = st.radio("Metode Pemilihan Berkas", ["Unggah Berkas", "Jalur Berkas Lokal (Path)"], horizontal=True)

source_file_path = None
uploaded_filename = None
file_size_mb = 0

if input_mode == "Unggah Berkas":
    uploaded = st.file_uploader(
        "Pilih berkas rekaman wawancara",
        type=["mp4", "mp3", "m4a", "wav", "mov", "mkv", "webm", "aac"],
        help="Format video MP4 dan audio MP3 didukung penuh. Batas unggahan hingga 4 GB."
    )
    if uploaded:
        uploaded_filename = uploaded.name
        file_size_mb = uploaded.size / (1024 * 1024)
        st.caption(f"Berkas: {uploaded.name} | Ukuran: {file_size_mb:.1f} MB")
else:
    direct_path = st.text_input(
        "Masukkan jalur lengkap berkas di komputer",
        placeholder="D:\\Rekaman\\wawancara_3_jam.mp4",
        help="Sangat berguna untuk file video berukuran sangat besar sehingga tidak perlu menunggu proses upload di browser."
    )
    if direct_path and os.path.exists(direct_path.strip('"')):
        source_file_path = direct_path.strip('"')
        uploaded_filename = Path(source_file_path).name
        file_size_mb = os.path.getsize(source_file_path) / (1024 * 1024)
        st.caption(f"Berkas terdeteksi: {uploaded_filename} | Ukuran: {file_size_mb:.1f} MB")
    elif direct_path:
        st.error("Jalur berkas tidak ditemukan di komputer.")

st.markdown("---")

# Tombol Aksi
can_proceed = bool(interview_title.strip() and (uploaded is not None if input_mode == "Unggah Berkas" else source_file_path is not None))

if not interview_title.strip():
    st.info("Harap isi Nama atau Judul Wawancara terlebih dahulu.")

if st.button("Mulai Transkripsi", type="primary", disabled=not can_proceed):
    final_title = interview_title.strip()
    temp_dir = tempfile.mkdtemp(prefix="transkrip_temp_")
    
    # Siapkan file sumber
    if input_mode == "Unggah Berkas":
        source_file_path = os.path.join(temp_dir, uploaded_filename)
        with open(source_file_path, "wb") as f:
            f.write(uploaded.getbuffer())

    try:
        progress_placeholder = st.empty()
        
        # Langkah 1: Ekstraksi dan penyiapan audio
        progress_placeholder.info("Menyiapkan dan mengekstrak audio dari berkas...")
        is_gemini = "Gemini" in engine_choice
        prepared_audio = prepare_audio(source_file_path, temp_dir, for_gemini=is_gemini)
        
        # Langkah 2: Proses Transkripsi
        transcript_result_text = ""
        
        if is_gemini:
            if not gemini_api_key.strip():
                raise ValueError("Kunci API Gemini belum dimasukkan. Silakan isi di menu sebelah kiri.")
            
            def update_gemini_status(msg):
                progress_placeholder.info(msg)
                
            transcript_result_text = transcribe_with_gemini(
                audio_path=prepared_audio,
                api_key=gemini_api_key,
                title=final_title,
                status_callback=update_gemini_status
            )
        else:
            progress_bar = st.progress(0, text="Memuat model Whisper dan memulai transkripsi lokal...")
            
            def update_whisper_progress(fraction):
                pct = int(fraction * 100)
                progress_bar.progress(min(99, pct), text=f"Transkripsi lokal berjalan... {pct}%")
                
            local_res = transcribe_audio(
                audio_path=prepared_audio,
                model_size=model_size,
                language="id",
                progress_callback=update_whisper_progress
            )
            progress_bar.progress(100, text="Transkripsi selesai.")
            transcript_result_text = build_txt_from_segments(local_res["segments"], include_timestamps=True)

        progress_placeholder.empty()

        if not transcript_result_text.strip():
            st.warning("Tidak ada teks percakapan yang berhasil dikenali.")
        else:
            # Langkah 3: Simpan otomatis ke folder terstruktur
            # Folder format: transkrip/HHMM_DDMMYYYY_Judul
            workspace_root = os.path.dirname(os.path.abspath(__file__))
            output_dir = create_output_directory(final_title, base_dir=workspace_root)
            safe_title = sanitize_folder_name(final_title)
            
            docx_target_path = os.path.join(output_dir, f"{safe_title}.docx")
            txt_target_path = os.path.join(output_dir, f"{safe_title}.txt")
            
            docx_bytes = build_docx(transcript_result_text, title=final_title, save_path=docx_target_path)
            txt_bytes = save_txt(transcript_result_text, save_path=txt_target_path)
            
            # Simpan state untuk UI
            st.session_state["last_transcript"] = transcript_result_text
            st.session_state["last_output_dir"] = output_dir
            st.session_state["last_title"] = final_title
            st.session_state["last_docx"] = docx_bytes
            st.session_state["last_txt"] = txt_bytes
            st.session_state["docx_path"] = docx_target_path
            st.session_state["txt_path"] = txt_target_path

    except Exception as exc:
        st.error("Proses transkripsi mengalami kendala.")
        st.code(str(exc))

# Tampilan Hasil Transkripsi
if "last_transcript" in st.session_state:
    output_dir = st.session_state["last_output_dir"]
    title = st.session_state["last_title"]
    safe_title = sanitize_folder_name(title)
    
    st.markdown(
        f"""
        <div class="success-box">
            <strong>Transkripsi Selesai dan Berkas Tersimpan</strong><br>
            Folder penyimpanan: <code>{output_dir}</code><br>
            Berkas Word: <code>{safe_title}.docx</code><br>
            Berkas Teks: <code>{safe_title}.txt</code>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tombol Aksi Penyimpanan dan Download
    action_c1, action_c2, action_c3 = st.columns([1, 1, 1])
    with action_c1:
        st.download_button(
            label="Unduh Dokumen Word (.docx)",
            data=st.session_state["last_docx"],
            file_name=f"{safe_title}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with action_c2:
        st.download_button(
            label="Unduh Berkas Teks (.txt)",
            data=st.session_state["last_txt"],
            file_name=f"{safe_title}.txt",
            mime="text/plain; charset=utf-8",
            use_container_width=True
        )
    with action_c3:
        if st.button("Buka Folder Penyimpanan", use_container_width=True):
            open_folder_in_explorer(output_dir)

    st.subheader("Pratinjau dan Koreksi Teks")
    edited_text = st.text_area(
        label="Teks hasil transkripsi dapat diedit langsung di bawah ini:",
        value=st.session_state["last_transcript"],
        height=450
    )
    
    # Jika user melakukan pengeditan teks di pratinjau, sediakan tombol perbarui berkas tersimpan
    if edited_text != st.session_state["last_transcript"]:
        if st.button("Simpan Perubahan ke Berkas"):
            docx_path = st.session_state["docx_path"]
            txt_path = st.session_state["txt_path"]
            new_docx = build_docx(edited_text, title=title, save_path=docx_path)
            new_txt = save_txt(edited_text, save_path=txt_path)
            st.session_state["last_transcript"] = edited_text
            st.session_state["last_docx"] = new_docx
            st.session_state["last_txt"] = new_txt
            st.success("Perubahan teks berhasil diperbarui di folder penyimpanan.")
            st.rerun()
