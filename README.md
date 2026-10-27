# Transkrip Wawancara Lokal

Aplikasi desktop/lokal berbasis Python & Streamlit untuk mentranskripsikan rekaman wawancara (berkas video `.mp4` dan audio `.mp3`) menjadi dokumen Bahasa Indonesia dalam format `.docx` (Microsoft Word) dan `.txt` (Teks).

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
