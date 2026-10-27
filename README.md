# Transkrip Wawancara Gratis

Aplikasi lokal Python + Streamlit untuk mentranskripsikan audio/video menjadi DOCX, TXT, atau SRT. Menggunakan faster-whisper; tidak memakai API berbayar.

## Kebutuhan
- Windows 10/11
- Python 3.10–3.12 (disarankan Python 3.11 64-bit)
- FFmpeg untuk ekstraksi audio dari video
- Ruang disk untuk model AI (diunduh saat pertama kali dipakai)
- Koneksi internet hanya untuk instalasi paket dan unduhan model pertama kali

## 1. Buat virtual environment
Buka PowerShell di folder proyek:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika aktivasi PowerShell diblokir, jalankan aplikasi menggunakan:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 2. Instal FFmpeg (untuk video)
Transkripsi file audio tidak memerlukan FFmpeg pada aplikasi ini. Untuk file video:
1. Instal FFmpeg build Windows dari situs resmi: https://ffmpeg.org/download.html
2. Tambahkan folder `bin` FFmpeg ke PATH Windows.
3. Tutup dan buka ulang terminal.
4. Pastikan berhasil:
```powershell
ffmpeg -version
```

## 3. Jalankan aplikasi
```powershell
streamlit run app.py
```
Browser akan membuka alamat lokal Streamlit, biasanya `http://localhost:8501`.

## Penggunaan
1. Unggah file audio/video yang didukung.
2. Pilih model. `base` adalah titik awal yang seimbang; `tiny` lebih ringan, `small`/`medium` lebih lambat tetapi dapat memberi hasil lebih baik.
3. Pilih bahasa atau deteksi otomatis.
4. Klik **Mulai Transkripsi**.
5. Periksa dan edit teks di kotak pratinjau.
6. Unduh DOCX, TXT, atau SRT.

## Privasi dan batasan
- Audio diproses di komputer sendiri. Model diunduh dari internet saat pertama kali dipakai; transkrip tidak dikirim ke API cloud oleh aplikasi ini.
- Untuk model yang sudah diunduh, proses transkripsi dapat berjalan offline.
- Hasil mesin harus diperiksa manual, khususnya nama orang, istilah, suara bising, dan percakapan tumpang tindih.
- Versi awal belum melakukan speaker diarization otomatis (pemisahan pembicara). Tambahkan label pembicara secara manual jika diperlukan.
- CPU dapat memproses rekaman panjang tetapi mungkin membutuhkan waktu cukup lama. Mulailah dengan model `base` atau `tiny`.
- Pastikan kamu punya izin untuk memproses rekaman wawancara yang berisi suara orang lain.
