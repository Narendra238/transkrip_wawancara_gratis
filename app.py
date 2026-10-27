import os
import tempfile
from pathlib import Path
import streamlit as st

from services.media_processor import prepare_audio
from services.transcriber import transcribe_audio
from exporters.export_txt import build_txt
from exporters.export_docx import build_docx
from exporters.export_srt import build_srt

st.set_page_config(page_title="Transkrip Wawancara", page_icon="🎙️", layout="wide")
st.title("🎙️ Transkrip Wawancara")
st.caption("Transkripsi audio/video secara lokal menggunakan faster-whisper. Tidak membutuhkan API berbayar.")

with st.sidebar:
    st.header("Pengaturan")
    model_size = st.selectbox(
        "Ukuran model",
        ["tiny", "base", "small", "medium"],
        index=1,
        help="tiny/base lebih cepat dan ringan. small/medium biasanya lebih akurat tetapi lebih lambat."
    )
    language_choice = st.selectbox(
        "Bahasa rekaman",
        ["Indonesia", "Deteksi otomatis", "Inggris"],
        index=0
    )
    language_map = {"Indonesia": "id", "Deteksi otomatis": None, "Inggris": "en"}
    include_timestamps = st.checkbox("Sertakan timestamp", value=True)
    st.info("Model diunduh saat pertama kali digunakan. Setelah model tersedia, transkripsi dapat berjalan tanpa internet.")

uploaded = st.file_uploader(
    "Unggah rekaman wawancara",
    type=["mp3", "wav", "m4a", "aac", "flac", "ogg", "wma", "mp4", "mov", "mkv", "webm", "mpeg", "mpg"],
    help="Audio dan video yang memiliki jalur audio didukung."
)

if uploaded:
    st.write(f"**File:** {uploaded.name} · **Ukuran:** {uploaded.size / (1024 * 1024):.1f} MB")
    if st.button("🚀 Mulai Transkripsi", type="primary", use_container_width=True):
        temp_dir = tempfile.mkdtemp(prefix="transkrip_")
        source_path = os.path.join(temp_dir, Path(uploaded.name).name)
        with open(source_path, "wb") as f:
            f.write(uploaded.getbuffer())

        try:
            with st.spinner("Menyiapkan audio..."):
                audio_path = prepare_audio(source_path, temp_dir)
            progress = st.progress(0, text="Memuat model dan mentranskripsikan audio...")
            result = transcribe_audio(
                audio_path=audio_path,
                model_size=model_size,
                language=language_map[language_choice],
                progress_callback=lambda fraction: progress.progress(
                    min(99, int(fraction * 100)),
                    text=f"Transkripsi berjalan... {int(fraction * 100)}%"
                )
            )
            progress.progress(100, text="Transkripsi selesai.")
            segments = result["segments"]
            if not segments:
                st.warning("Tidak ada ucapan yang berhasil dikenali. Coba model lebih besar atau periksa kualitas rekaman.")
            else:
                st.success(f"Berhasil membuat transkrip: {len(segments)} segmen.")
                st.caption(f"Bahasa terdeteksi: {result.get('language') or 'tidak diketahui'}")
                transcript_text = build_txt(segments, include_timestamps)
                st.subheader("Pratinjau transkrip")
                edited_text = st.text_area(
                    "Kamu bisa mengoreksi hasil sebelum mengunduh.",
                    value=transcript_text,
                    height=360
                )
                safe_stem = Path(uploaded.name).stem
                docx_bytes = build_docx(edited_text, title=f"Transkrip Wawancara - {safe_stem}")
                txt_bytes = edited_text.encode("utf-8")
                srt_bytes = build_srt(segments).encode("utf-8")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.download_button("⬇️ Unduh DOCX", docx_bytes,
                        file_name=f"{safe_stem}_transkrip.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True)
                with c2:
                    st.download_button("⬇️ Unduh TXT", txt_bytes,
                        file_name=f"{safe_stem}_transkrip.txt",
                        mime="text/plain; charset=utf-8", use_container_width=True)
                with c3:
                    st.download_button("⬇️ Unduh SRT", srt_bytes,
                        file_name=f"{safe_stem}_transkrip.srt",
                        mime="text/plain; charset=utf-8", use_container_width=True)
        except Exception as exc:
            st.error("Transkripsi gagal. Periksa pesan di bawah dan ikuti petunjuk instalasi di README.")
            st.code(str(exc))
        finally:
            # Keep temporary files until the Streamlit rerun completes; clean-up is handled by OS/temp cleanup.
            pass
else:
    st.markdown("""
    **Cara pakai**
    1. Unggah file audio atau video.
    2. Pilih ukuran model dan bahasa.
    3. Klik **Mulai Transkripsi**.
    4. Periksa/koreksi teks, lalu unduh DOCX, TXT, atau SRT.

    **Catatan:** versi awal ini belum memisahkan pembicara secara otomatis. Nama pewawancara/narasumber dapat ditambahkan atau dikoreksi secara manual.
    """)
