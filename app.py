import os
import tempfile
import importlib
from pathlib import Path
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import services.media_processor
import services.gemini_transcriber
import services.transcriber
import services.storage_manager
import exporters.export_docx
import exporters.export_txt

# Paksa reload modul agar Streamlit selalu menggunakan kode terbaru dari disk tanpa perlu restart
try:
    importlib.reload(services.gemini_transcriber)
    importlib.reload(services.transcriber)
    importlib.reload(exporters.export_docx)
except Exception:
    pass

from services.media_processor import prepare_audio
from services.gemini_transcriber import (
    transcribe_with_gemini,
    refine_transcript_with_ai,
    load_saved_api_key
)
from services.transcriber import transcribe_audio, is_cuda_available
from services.storage_manager import create_output_directory, sanitize_folder_name, open_folder_in_explorer
from exporters.export_docx import build_docx
from exporters.export_txt import build_txt_from_segments, save_txt

def safe_build_docx(transcript_text: str, title: str, language_label: str = "Bahasa Indonesia", save_path: str = None) -> bytes:
    """Wrapper aman untuk build_docx yang toleran terhadap perbedaan versi modul di RAM."""
    try:
        return build_docx(transcript_text, title=title, language_label=language_label, save_path=save_path)
    except TypeError:
        return build_docx(transcript_text, title=title, save_path=save_path)

# Konfigurasi Halaman - Minimalis, bersih, tanpa ikon/simbol
st.set_page_config(
    page_title="Transkrip Wawancara",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan elegan profesional
st.markdown("""
<style>
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
    .info-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.88rem;
        color: #334155;
    }
    .stButton>button {
        border-radius: 4px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Header Halaman
st.markdown('<div class="main-title">Transkrip Wawancara</div>', unsafe_allow_html=True)
st.markdown('<div class="main-desc">Pengubah rekaman wawancara video dan audio menjadi dokumen teks (Bahasa Indonesia, Inggris, Arab, Mandarin, Jerman, Spanyol) dalam format DOCX dan TXT.</div>', unsafe_allow_html=True)

# Otomatis baca API Key dari api_key.txt atau .env
saved_api_key = load_saved_api_key()
has_gpu = is_cuda_available()

LANGUAGE_OPTIONS = {
    "id": "Bahasa Indonesia (Default)",
    "en": "Bahasa Inggris (English)",
    "ar": "Bahasa Arab (العربية)",
    "zh": "Bahasa Mandarin (中文 / Hanzi)",
    "de": "Bahasa Jerman (Deutsch)",
    "es": "Bahasa Spanyol (Español)",
    "auto": "Deteksi Otomatis (Auto-Detect)"
}

# Panel Samping (Pengaturan)
with st.sidebar:
    st.subheader("Pengaturan Transkripsi")

    selected_language = st.selectbox(
        "Bahasa Rekaman (Audio Language)",
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda x: LANGUAGE_OPTIONS[x],
        index=0,
        help="Pilih bahasa audio wawancara. Hasil transkrip akan tetap dalam bahasa aslinya (Verbatim Original) tanpa diterjemahkan."
    )

    engine_choice = st.radio(
        "Metode Transkripsi Utama",
        [
            "Google Gemini (Online Cloud - Sangat Cepat 1-2 Menit)",
            "Whisper Lokal (Offline di Komputer)"
        ],
        index=0 if saved_api_key else 1,
        help="Google Gemini menggunakan kuota gratis dari Google AI Studio dan memproses video berjam-jam dalam hitungan menit."
    )

    selected_hardware = "cpu"
    if "Whisper Lokal" in engine_choice:
        hw_options = ["GPU NVIDIA RTX 4060 (Sangat Cepat - Aktif)", "CPU (Standar)"]
        chosen_hw = st.radio(
            "Perangkat Keras Pemrosesan",
            hw_options,
            index=0,
            help="GPU NVIDIA RTX 4060 laptop Anda sudah aktif dan siap mempercepat transkripsi hingga 10x-15x lipat."
        )
        selected_hardware = "cuda" if "GPU" in chosen_hw else "cpu"

        model_size = st.selectbox(
            "Ukuran Model Whisper",
            ["tiny", "base", "small", "medium"],
            index=1,
            help="Model 'base' adalah titik awal yang seimbang antara kecepatan dan akurasi."
        )

        include_timestamps = st.checkbox(
            "Sertakan penanda waktu [HH:MM:SS]",
            value=False,
            help="Secara default tidak dicentang agar hasil bersih mengalir dalam bentuk paragraf percakapan (seperti TurboScribe)."
        )

    st.markdown("---")
    st.subheader("Penyempurnaan Teks AI")
    auto_refine = st.checkbox(
        "Otomatis sempurnakan teks dengan AI setelah transkrip",
        value=False,
        help="Opsional: AI Gemini akan mengoreksi typo dan ejaan. Matikan opsi ini jika ingin hasil instan langsung tersimpan."
    )

    api_key_input = st.text_input(
        "Gemini API Key",
        value=saved_api_key,
        type="password",
        help="API Key otomatis dibaca dari api_key.txt atau .env jika sudah ada."
    )

    if saved_api_key:
        st.caption("Kunci API Gemini aktif terdeteksi.")
    else:
        st.caption("Masukkan API Key gratis dari Google AI Studio jika ingin menggunakan fitur penyempurna ejaan AI.")

    st.markdown("---")
    st.markdown(
        "<small style='color: #64748b;'>"
        "Folder penyimpanan otomatis:<br>"
        "<code>transkrip/HHMM_DDMMYYYY_Judul/</code>"
        "</small>",
        unsafe_allow_html=True
    )

# Area Formulir Utama
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.subheader("1. Identitas Rekaman")
    interview_title = st.text_input(
        "Nama atau Judul Wawancara",
        placeholder="Contoh: Wawancara Narasumber A - Topik Evaluasi",
        help="Judul ini akan digunakan sebagai penamaan folder hasil dan judul dokumen resmi."
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
        help="Format video MP4 dan audio MP3 didukung hingga 4 GB."
    )
    if uploaded:
        uploaded_filename = uploaded.name
        file_size_mb = uploaded.size / (1024 * 1024)
        st.caption(f"Berkas: {uploaded.name} | Ukuran: {file_size_mb:.1f} MB")
else:
    direct_path = st.text_input(
        "Masukkan jalur lengkap berkas di komputer",
        placeholder="D:\\Rekaman\\wawancara.mp4",
        help="Sangat praktis untuk file besar agar tidak perlu upload ulang di peramban."
    )
    if direct_path and os.path.exists(direct_path.strip('"')):
        source_file_path = direct_path.strip('"')
        uploaded_filename = Path(source_file_path).name
        file_size_mb = os.path.getsize(source_file_path) / (1024 * 1024)
        st.caption(f"Berkas terdeteksi: {uploaded_filename} | Ukuran: {file_size_mb:.1f} MB")
    elif direct_path:
        st.error("Jalur berkas tidak ditemukan di komputer.")

st.markdown("---")

can_proceed = bool(interview_title.strip() and (uploaded is not None if input_mode == "Unggah Berkas" else source_file_path is not None))

if not interview_title.strip():
    st.info("Harap isi Nama atau Judul Wawancara terlebih dahulu.")

if st.button("Mulai Transkripsi", type="primary", disabled=not can_proceed):
    final_title = interview_title.strip()
    temp_dir = tempfile.mkdtemp(prefix="transkrip_temp_")
    active_api_key = api_key_input.strip() or saved_api_key

    if input_mode == "Unggah Berkas":
        source_file_path = os.path.join(temp_dir, uploaded_filename)
        with open(source_file_path, "wb") as f:
            f.write(uploaded.getbuffer())

    try:
        progress_placeholder = st.empty()
        is_gemini_main = "Gemini" in engine_choice
        
        # 1. Ekstraksi dan penyiapan audio
        progress_placeholder.info("Menyiapkan dan mengekstrak audio dari berkas...")
        prepared_audio = prepare_audio(source_file_path, temp_dir, for_gemini=is_gemini_main)

        transcript_result_text = ""

        # 2. Proses Transkripsi
        if is_gemini_main:
            if not active_api_key:
                raise ValueError("API Key Gemini belum diisi. Masukkan kunci API di panel sebelah kiri.")
            
            def update_gemini_status(msg):
                progress_placeholder.info(msg)

            transcript_result_text = transcribe_with_gemini(
                audio_path=prepared_audio,
                api_key=active_api_key,
                title=final_title,
                language_code=selected_language,
                status_callback=update_gemini_status
            )
        else:
            progress_bar = st.progress(0, text="Memuat model Whisper...")
            
            def update_whisper_progress(fraction, status_text):
                progress_bar.progress(fraction, text=f"Transkripsi berjalan... {status_text}")

            whisper_lang = None if selected_language == "auto" else selected_language
            local_res = transcribe_audio(
                audio_path=prepared_audio,
                model_size=model_size,
                language=whisper_lang,
                device=selected_hardware,
                progress_callback=update_whisper_progress
            )
            use_ts = include_timestamps if "Whisper Lokal" in engine_choice else False
            transcript_result_text = build_txt_from_segments(local_res["segments"], include_timestamps=use_ts)

        if not transcript_result_text.strip():
            st.warning("Tidak ada teks percakapan yang berhasil dikenali.")
        else:
            # 3. Simpan Langsung ke Folder Hasil (Instan & Aman)
            workspace_root = os.path.dirname(os.path.abspath(__file__))
            output_dir = create_output_directory(final_title, base_dir=workspace_root)
            safe_title = sanitize_folder_name(final_title)

            docx_target_path = os.path.join(output_dir, f"{safe_title}.docx")
            txt_target_path = os.path.join(output_dir, f"{safe_title}.txt")

            lang_label = LANGUAGE_OPTIONS.get(selected_language, "Bahasa Indonesia")
            docx_bytes = safe_build_docx(transcript_result_text, title=final_title, language_label=lang_label, save_path=docx_target_path)
            txt_bytes = save_txt(transcript_result_text, save_path=txt_target_path)

            st.session_state["last_transcript"] = transcript_result_text
            st.session_state["last_output_dir"] = output_dir
            st.session_state["last_title"] = final_title
            st.session_state["last_docx"] = docx_bytes
            st.session_state["last_txt"] = txt_bytes
            st.session_state["docx_path"] = docx_target_path
            st.session_state["txt_path"] = txt_target_path
            st.session_state["last_language"] = selected_language
            st.session_state["last_lang_label"] = lang_label

            # 4. Fitur Penyempurnaan AI Otomatis (jika dicentang)
            if auto_refine and active_api_key:
                try:
                    def update_refine_status(msg):
                        progress_placeholder.info(msg)

                    progress_placeholder.info("Menyempurnakan ejaan dan tanda baca dengan AI...")
                    refined = refine_transcript_with_ai(
                        transcript_text=transcript_result_text,
                        api_key=active_api_key,
                        language_code=selected_language,
                        status_callback=update_refine_status
                    )
                    if refined and refined.strip():
                        transcript_result_text = refined
                        docx_bytes = safe_build_docx(transcript_result_text, title=final_title, language_label=lang_label, save_path=docx_target_path)
                        txt_bytes = save_txt(transcript_result_text, save_path=txt_target_path)
                        st.session_state["last_transcript"] = transcript_result_text
                        st.session_state["last_docx"] = docx_bytes
                        st.session_state["last_txt"] = txt_bytes
                except Exception as refine_err:
                    st.warning(f"Penyempurnaan AI otomatis dilewati ({refine_err}). Berkas hasil transkripsi asli tetap aman tersimpan.")

            progress_placeholder.empty()

    except Exception as exc:
        st.error("Proses transkripsi mengalami kendala.")
        st.code(str(exc))

# Tampilan Hasil Transkripsi
if "last_transcript" in st.session_state:
    output_dir = st.session_state["last_output_dir"]
    title = st.session_state["last_title"]
    safe_title = sanitize_folder_name(title)
    active_api_key = api_key_input.strip() or saved_api_key
    cur_lang_label = st.session_state.get("last_lang_label", LANGUAGE_OPTIONS.get(selected_language, "Bahasa Indonesia"))

    st.markdown(
        f"""
        <div class="success-box">
            <strong>Transkripsi Selesai dan Berkas Tersimpan</strong><br>
            Bahasa Rekaman: <strong>{cur_lang_label}</strong><br>
            Folder penyimpanan: <code>{output_dir}</code><br>
            Berkas Word: <code>{safe_title}.docx</code><br>
            Berkas Teks: <code>{safe_title}.txt</code>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    st.markdown("---")

    # Fitur Penyempurnaan Teks dengan AI (Tombol Manual)
    refine_col1, refine_col2 = st.columns([2, 1])
    with refine_col1:
        st.subheader("Pratinjau Hasil Transkripsi")
    with refine_col2:
        if st.button("Sempurnakan Teks dengan AI (Perbaiki Typo & Ejaan)", use_container_width=True):
            if not active_api_key:
                st.error("Harap isi Gemini API Key di panel kiri atau buat berkas api_key.txt.")
            else:
                current_lang = st.session_state.get("last_language", selected_language)
                current_label = st.session_state.get("last_lang_label", LANGUAGE_OPTIONS.get(current_lang, "Bahasa Indonesia"))
                with st.spinner("AI sedang memeriksa dan menyempurnakan ejaan teks..."):
                    refined_text = refine_transcript_with_ai(
                        transcript_text=st.session_state["last_transcript"],
                        api_key=active_api_key,
                        language_code=current_lang
                    )
                    docx_path = st.session_state["docx_path"]
                    txt_path = st.session_state["txt_path"]
                    new_docx = safe_build_docx(refined_text, title=title, language_label=current_label, save_path=docx_path)
                    new_txt = save_txt(refined_text, save_path=txt_path)
                    st.session_state["last_transcript"] = refined_text
                    st.session_state["last_docx"] = new_docx
                    st.session_state["last_txt"] = new_txt
                    st.success("Teks berhasil disempurnakan dan berkas DOCX & TXT di folder penyimpanan telah diperbarui otomatis.")
                    st.rerun()

    edited_text = st.text_area(
        label="Teks dapat dikoreksi manual secara langsung di kotak ini:",
        value=st.session_state["last_transcript"],
        height=450
    )

    if edited_text != st.session_state["last_transcript"]:
        if st.button("Simpan Perubahan Manual ke Berkas"):
            current_label = st.session_state.get("last_lang_label", LANGUAGE_OPTIONS.get(selected_language, "Bahasa Indonesia"))
            docx_path = st.session_state["docx_path"]
            txt_path = st.session_state["txt_path"]
            new_docx = safe_build_docx(edited_text, title=title, language_label=current_label, save_path=docx_path)
            new_txt = save_txt(edited_text, save_path=txt_path)
            st.session_state["last_transcript"] = edited_text
            st.session_state["last_docx"] = new_docx
            st.session_state["last_txt"] = new_txt
            st.success("Perubahan manual berhasil diperbarui di folder penyimpanan.")
            st.rerun()
