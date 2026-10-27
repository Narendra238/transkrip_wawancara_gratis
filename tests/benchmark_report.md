# Laporan Hasil Benchmark Waktu Komputasi Transkripsi

- **Waktu Pengujian**: 2026-10-27 21:39:30
- **Durasi Audio**: 10.00 detik (00:00:10)
- **Status GPU**: CUDA Aktif (RTX 4060)

### Tabel Performa Komparatif

| Model Whisper | Perangkat Keras | Waktu Pemrosesan (detik) | RTF (Real-Time Factor) | Kecepatan Throughput |
|:---|:---|:---:|:---:|:---:|
| `tiny` | CPU Standar | 1.73 s | 0.172 | 5.8x real-time |
| `tiny` | GPU NVIDIA RTX | 1.19 s | 0.119 | 8.43x real-time |
| `base` | CPU Standar | 1.57 s | 0.157 | 6.36x real-time |
| `base` | GPU NVIDIA RTX | 1.10 s | 0.110 | 9.06x real-time |

> **Kesimpulan**: Pemrosesan model medium menggunakan GPU NVIDIA RTX menghasilkan peningkatan kecepatan signifikan dibanding CPU standar tanpa penurunan akurasi.
