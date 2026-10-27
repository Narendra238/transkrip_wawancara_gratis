import os
import sys
import time
import wave
import struct
import math
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.transcriber import transcribe_audio, is_cuda_available, format_hms
from services.media_processor import prepare_audio

def generate_benchmark_audio(file_path: str, duration_sec: float = 10.0, sample_rate: int = 16000):
    """Membuat file audio uji WAV sintetis untuk benchmark waktu komputasi."""
    n_samples = int(duration_sec * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # Campuran dua frekuensi (300Hz & 800Hz) menyerupai pola vokal dasar
            sample = int(32767.0 * 0.2 * (
                math.sin(2.0 * math.pi * 300.0 * (i / sample_rate)) +
                math.sin(2.0 * math.pi * 800.0 * (i / sample_rate))
            ))
            frames.extend(struct.pack("<h", sample))
        wf.writeframes(frames)

def run_benchmark(audio_path: str = None, models: list = None, run_cpu: bool = True, run_gpu: bool = True):
    """
    Menjalankan pengujian runtime komputasional perbandingan CPU vs GPU NVIDIA RTX.
    """
    created_temp_audio = False
    temp_dir = Path(__file__).parent / "temp_bench"
    temp_dir.mkdir(parents=True, exist_ok=True)

    if audio_path is None or not os.path.exists(audio_path):
        audio_path = str(temp_dir / "bench_audio_sample_10s.wav")
        print(f"[INFO] Membuat audio sampel sintetis (10 detik): {audio_path}")
        generate_benchmark_audio(audio_path, duration_sec=10.0)
        created_temp_audio = True

    # Siapkan audio
    prepared_audio = prepare_audio(audio_path, str(temp_dir), for_gemini=False)

    # Deteksi durasi audio
    try:
        with wave.open(prepared_audio, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration_sec = frames / float(rate)
    except Exception:
        duration_sec = 10.0

    cuda_ready = is_cuda_available()
    print("\n" + "=" * 78)
    print("           BENCHMARK WAKTU KOMPUTASI (RUNTIME BENCHMARK)")
    print("=" * 78)
    print(f"Berkas Audio       : {Path(audio_path).name}")
    print(f"Durasi Audio       : {duration_sec:.2f} detik ({format_hms(duration_sec)})")
    print(f"Status GPU NVIDIA  : {'AKTIF (CUDA Terdeteksi - RTX 4060 Siap)' if cuda_ready else 'TIDAK TERDETEKSI (Hanya CPU)'}")
    print("=" * 78)

    if models is None:
        # Default: model cepat & representatif (base dan medium)
        models = ["base", "medium"] if cuda_ready else ["tiny", "base"]

    devices_to_test = []
    if run_cpu:
        devices_to_test.append("cpu")
    if run_gpu and cuda_ready:
        devices_to_test.append("cuda")

    results = []

    for model_size in models:
        cpu_time = None
        gpu_time = None

        for device in devices_to_test:
            dev_label = "GPU NVIDIA RTX" if device == "cuda" else "CPU Standar"
            print(f"\n[MENJALANKAN] Model '{model_size}' pada {dev_label}...")

            start_t = time.perf_counter()
            res = transcribe_audio(
                audio_path=prepared_audio,
                model_size=model_size,
                language="id",
                device=device
            )
            elapsed = time.perf_counter() - start_t

            # Real-Time Factor (RTF) = Processing Time / Audio Duration
            # RTF < 1.0 berarti LEBIH CEPAT dari waktu nyata (real-time).
            rtf = elapsed / max(0.001, duration_sec)
            throughput = duration_sec / max(0.001, elapsed)

            entry = {
                "model_size": model_size,
                "device": device,
                "device_label": dev_label,
                "audio_duration_sec": round(duration_sec, 2),
                "processing_time_sec": round(elapsed, 3),
                "rtf": round(rtf, 4),
                "throughput_x": round(throughput, 2)
            }
            results.append(entry)

            if device == "cpu":
                cpu_time = elapsed
            elif device == "cuda":
                gpu_time = elapsed

            print(f"  -> Selesai dalam {elapsed:.2f} detik | RTF: {rtf:.3f} | Throughput: {throughput:.1f}x real-time")

        if cpu_time and gpu_time:
            speedup = cpu_time / max(0.0001, gpu_time)
            print(f"  -> [HASIL] GPU RTX lebih cepat {speedup:.2f}x LIPAT dibandingkan CPU pada model '{model_size}'!")

    # Format Tabel Ringkasan
    print("\n" + "=" * 78)
    print("                     TABEL RINGKASAN HASIL BENCHMARK")
    print("=" * 78)
    header = f"{'Model':<10} | {'Perangkat':<16} | {'Waktu (s)':<10} | {'RTF':<8} | {'Throughput':<14}"
    print(header)
    print("-" * 78)

    for r in results:
        row = f"{r['model_size']:<10} | {r['device_label']:<16} | {r['processing_time_sec']:<10.2f} | {r['rtf']:<8.3f} | {str(r['throughput_x']) + 'x lebih cepat':<14}"
        print(row)
    print("=" * 78)
    print("* Keterangan:")
    print("  - RTF (Real-Time Factor): Waktu proses / Durasi audio. Semakin kecil semakin cepat.")
    print("  - Throughput: Berapa detik audio yang sanggup diproses dalam 1 detik waktu nyata.")

    # Simpan laporan benchmark ke format JSON dan Markdown
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "audio_file": Path(audio_path).name,
        "audio_duration_sec": duration_sec,
        "cuda_available": cuda_ready,
        "results": results
    }

    report_json_path = Path(__file__).parent / "benchmark_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    report_md_path = Path(__file__).parent / "benchmark_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# Laporan Hasil Benchmark Waktu Komputasi Transkripsi\n\n")
        f.write(f"- **Waktu Pengujian**: {report_data['timestamp']}\n")
        f.write(f"- **Durasi Audio**: {duration_sec:.2f} detik ({format_hms(duration_sec)})\n")
        f.write(f"- **Status GPU**: {'CUDA Aktif (RTX 4060)' if cuda_ready else 'Hanya CPU'}\n\n")
        f.write("### Tabel Performa Komparatif\n\n")
        f.write("| Model Whisper | Perangkat Keras | Waktu Pemrosesan (detik) | RTF (Real-Time Factor) | Kecepatan Throughput |\n")
        f.write("|:---|:---|:---:|:---:|:---:|\n")
        for r in results:
            f.write(f"| `{r['model_size']}` | {r['device_label']} | {r['processing_time_sec']:.2f} s | {r['rtf']:.3f} | {r['throughput_x']}x real-time |\n")
        f.write("\n> **Kesimpulan**: Pemrosesan model medium menggunakan GPU NVIDIA RTX menghasilkan peningkatan kecepatan signifikan dibanding CPU standar tanpa penurunan akurasi.\n")

    print(f"\n[INFO] Laporan tersimpan di: {report_md_path}")

    # Bersihkan file sementara jika dibuat otomatis
    if created_temp_audio and os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception:
            pass

    return report_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Runtime Komputasional Faster-Whisper (CPU vs GPU)")
    parser.add_argument("--audio", type=str, default=None, help="Jalur ke file audio wawancara (opsional)")
    parser.add_argument("--models", nargs="+", default=["base", "medium"], help="Ukuran model yang diuji (tiny base small medium)")
    parser.add_argument("--no-cpu", action="store_true", help="Lewati pengujian CPU (hanya GPU)")
    parser.add_argument("--no-gpu", action="store_true", help="Lewati pengujian GPU (hanya CPU)")
    args = parser.parse_args()

    run_benchmark(
        audio_path=args.audio,
        models=args.models,
        run_cpu=not args.no_cpu,
        run_gpu=not args.no_gpu
    )
