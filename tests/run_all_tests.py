import os
import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def main():
    start_all = time.perf_counter()
    print_banner("Menjalankan Suite Pengujian Lengkap (Testing Suite)")
    print("1. Unit Testing        : Memeriksa fungsi utilitas, format teks, docx, dan SUS")
    print("2. Functional Testing  : Memeriksa alur ekspor multibahasa dan survei SUS")
    print("3. Integration Testing : Memeriksa pipeline transkripsi end-to-end dengan audio")
    print("-" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Muat test dari masing-masing file
    suite.addTests(loader.discover(start_dir=str(Path(__file__).parent), pattern="test_unit.py"))
    suite.addTests(loader.discover(start_dir=str(Path(__file__).parent), pattern="test_functional.py"))
    suite.addTests(loader.discover(start_dir=str(Path(__file__).parent), pattern="test_integration.py"))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed_all = time.perf_counter() - start_all
    print("\n" + "=" * 70)
    print("                        RINGKASAN HASIL PENGUJIAN")
    print("=" * 70)
    print(f"Total Tes Dijalankan : {result.testsRun}")
    print(f"Berhasil (Passed)    : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Gagal (Failures)     : {len(result.failures)}")
    print(f"Error (Errors)       : {len(result.errors)}")
    print(f"Waktu Eksekusi Total : {elapsed_all:.2f} detik")
    print("=" * 70)

    if result.wasSuccessful():
        print("[STATUS] SEMUA PENGUJIAN LULUS (ALL TESTS PASSED) DENGAN SEMPURNA!")
        print("Aplikasi siap untuk tahap rilis (release) dan pengujian pengguna (SUS).")
        return 0
    else:
        print("[STATUS] BEBERAPA PENGUJIAN GAGAL. SILAKAN CEK DETAIL LOG DI ATAS.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
