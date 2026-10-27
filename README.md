# Transkrip Wawancara Lokal & Multibahasa

Aplikasi desktop/lokal berbasis Python & Streamlit untuk mentranskripsikan rekaman wawancara (berkas video `.mp4` dan audio `.mp3`) menjadi dokumen teks profesional dalam format `.docx` (Microsoft Word) dan `.txt` (Teks). Mendukung Bahasa Indonesia (default), Inggris, Arab, Mandarin, Jerman, Spanyol, dan Deteksi Otomatis secara verbatim asli.

---

## Mengapa Rekaman Video 3 Jam Sebelumnya Gagal?

1. **Batas Ukuran Berkas Bawaan Streamlit (200 MB)**:
   Video MP4 berdurasi 3 jam biasanya berukuran antara 500 MB hingga 3 GB. Streamlit secara default menolak berkas di atas 200 MB kecuali dikonfigurasi melalui `server.maxUploadSize`.
2. **Ketiadaan FFmpeg di PATH Sistem**:
   Pengekstrakan audio dari berkas MP4 membutuhkan FFmpeg. Jika FFmpeg belum terpasang atau belum didaftarkan di Environment Variables Windows, aplikasi akan langsung terhenti dengan galat.
3. **Beban Komputasi CPU Whisper Lokal**:
   Model Whisper yang diproses langsung di CPU komputer memerlukan waktu 1 hingga 2 jam untuk berkas 3 jam, yang dapat memicu kehabisan memori (RAM) atau koneksi peramban terputus.

---

## Solusi dan Fitur Baru

- **Dukungan Durasi Panjang (Hingga 4 GB)**: Konfigurasi unggahan telah dinaikkan hingga 4.096 MB, serta tersedia opsi input jalur berkas lokal (*direct path*) agar tidak perlu menunggu proses pengunggahan di peramban.
- **FFmpeg Terintegrasi Otomatis**: Memanfaatkan pustaka `imageio-ffmpeg` bawaan di `venv`, sehingga Anda tidak perlu memasang atau mengatur PATH FFmpeg secara manual di Windows.
- **Model AI Cepat & Gratis (Google Gemini API)**:
  - Menggunakan API gratis dari Google AI Studio (`gemini-2.0-flash` / `gemini-1.5-flash`).
  - Rekaman audio 3 jam dapat diselesaikan hanya dalam waktu **1–2 menit**.
  - Menghasilkan Bahasa Indonesia yang alami, peka konteks percakapan, serta memisahkan pembicara dan penanda waktu secara otomatis.
- **Whisper Lokal (Offline)**: Tetap tersedia bagi pengguna yang ingin memproses tanpa koneksi internet.
- **Penamaan Folder Otomatis**:
  Hasil disimpan langsung di:
  `transkrip/HHMM_DDMMYYYY_JudulWawancara/`
  Contoh: `transkrip/0753_27102026_Wawancara_NarasumberA/`
  Di dalamnya langsung tersimpan berkas `.docx` dan `.txt`.
- **Inisiasi Judul di Awal**: Pengguna mengisi nama/judul wawancara sebelum tombol proses ditekan.
- **Tampilan Bersih & Bebas Ikon AI**: Desain minimalis, formal, dan rapi tanpa emoji atau simbol dekoratif.

---

## Cara Menjalankan Aplikasi

### Cara 1: Menggunakan File Batch (Paling Praktis)
Cukup klik dua kali (*double-click*) berkas:
```
jalankan.bat
```
Aplikasi akan otomatis mengaktifkan lingkungan virtual (`venv`) dan membuka peramban di alamat `http://localhost:8501`.

### Cara 2: Melalui Terminal (PowerShell)
```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

---

## Panduan Penggunaan

1. **Isi Judul Wawancara**: Masukkan nama narasumber atau topik wawancara.
2. **Pilih Sumber Berkas**:
   - Unggah berkas `.mp4` atau `.mp3` langsung melalui formulir, **atau**
   - Masukkan jalur (*path*) berkas lokal di komputer jika berkas berukuran sangat besar.
3. **Pilih Metode Transkripsi**:
   - **Google Gemini (Disarankan)**: Masukkan API key gratis dari [Google AI Studio](https://aistudio.google.com/app/apikey). Anda bisa menekan tombol "Simpan API Key" agar tersimpan permanen di komputer lokal Anda.
   - **Whisper Lokal**: Untuk pemrosesan offline tanpa internet.
4. **Klik "Mulai Transkripsi"**: Sistem akan mengekstrak audio, memproses transkrip, dan langsung menyimpan hasilnya di folder `transkrip/`.
5. **Koreksi & Unduh**: Pratinjau teks dapat diedit langsung, dan berkas Word/TXT dapat diunduh atau dibuka langsung melalui tombol "Buka Folder Penyimpanan".

---

## Suite Pengujian (Testing Suite)

Tersedia rangkaian pengujian otomatis lengkap untuk memastikan keandalan sebelum rilis (*release*):

- **Unit Testing** (`tests/test_unit.py`): Memeriksa 20 fungsi terisolasi (ekspor docx, format txt, sanitasi folder, kalkulasi SUS, utilitas waktu).
- **Functional Testing** (`tests/test_functional.py`): Memeriksa 5 alur fitur (ekspor multibahasa Arab/Hanzi/Jerman/Spanyol, penyiapan media, siklus hidup kuesioner SUS).
- **Integration Testing** (`tests/test_integration.py`): Memeriksa pipeline transkripsi audio nyata dari input WAV sintetis hingga penyimpanan fisik DOCX & TXT di disk.
- **Runtime Benchmark** (`tests/test_benchmark_runtime.py`): Mengukur performa komputasi Real-Time Factor (RTF), Throughput, dan rasio percepatan GPU RTX vs CPU.

### Cara Menjalankan Pengujian:
```bat
jalankan_testing.bat
```
Atau melalui terminal:
```powershell
.\venv\Scripts\python.exe tests\run_all_tests.py
.\venv\Scripts\python.exe tests\test_benchmark_runtime.py
```

---

## Evaluasi Usability Pengguna (SUS - System Usability Scale)

Aplikasi telah dilengkapi formulir kuesioner **System Usability Scale (SUS)** standar John Brooke (1986):
1. Buka tab **"Evaluasi Usability (Form SUS)"** di antarmuka web.
2. Responden mengisi 10 butir pertanyaan skala Likert (1 - 5).
3. Skor otomatis dihitung seketika (0 - 100) lengkap dengan *Grade Usability* (A/B/C/F), *Adjective Rating* (Excellent/Good/OK/Poor), dan *Acceptability*.
4. Data tersimpan permanen di `evaluasi_sus/hasil_evaluasi_sus.csv` dan dapat diunduh langsung untuk lampiran laporan riset.
5. Tersedia dokumen kuesioner siap cetak di `evaluasi_sus/KUESIONER_SUS.md`.

---

## Panduan Deployment GPU (Apakah Harus RTX 4060?)

- **Apakah harus GPU yang sama persis (RTX 4060)?**  
  **TIDAK HARUS**. Pustaka `ctranslate2` dan runtime NVIDIA CUDA kompatibel dengan **seluruh kartu grafis NVIDIA** yang mendukung CUDA Compute Capability >= 5.0.
- **Pilihan GPU yang Didukung**:
  - **PC / Laptop Lokal**: GTX 1650/1660, RTX 2060, RTX 3050, RTX 3060, RTX 4060, RTX 4070, RTX 4080, RTX 4090.
  - **Cloud Server (RunPod, Vast.ai, AWS, GCP)**: NVIDIA T4 (16GB VRAM - paling ekonomis ~$0.20/jam), NVIDIA A10G (24GB), L4, atau A100.
- **Kebutuhan VRAM Model Whisper**:
  - `tiny`: ~1 GB VRAM
  - `base`: ~1.5 GB VRAM
  - `small`: ~2.5 GB VRAM
  - `medium`: ~5 GB VRAM (RTX 4060 8GB sangat optimal)
  - `large-v3`: ~10 GB VRAM
- **Jika Deploy di Layanan Cloud Gratis (Streamlit Cloud / Render / Vercel)**:
  - Layanan gratis umumnya hanya menyediakan CPU tanpa GPU.
  - **Solusi**: Pengguna cukup memilih metode **Google Gemini API** yang tetap gratis, super cepat (1–2 menit), diproses di cloud Google, dan tidak memerlukan sewa server GPU berbayar.
