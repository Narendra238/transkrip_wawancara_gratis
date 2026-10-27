@echo off
title Testing Suite - Transkrip Wawancara
cd /d "%~dp0"

echo ==============================================================
echo        MENJALANKAN TESTING SUITE TRANSKRIP WAWANCARA
echo ==============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual Environment belum terpasang di folder venv.
    pause
    exit /b 1
)

echo Menjalankan Unit Testing, Functional Testing, dan Integration Testing...
echo.
.\venv\Scripts\python.exe tests\run_all_tests.py

echo.
echo ==============================================================
echo Ingin menjalankan Benchmark Waktu Komputasi (CPU vs GPU)?
echo Tekan 'Y' untuk menjalankan, atau sembarang tombol untuk selesai.
echo ==============================================================
set /p user_choice="Pilihan Anda (Y/N): "
if /i "%user_choice%"=="Y" (
    echo.
    echo Menjalankan Runtime Benchmark...
    .\venv\Scripts\python.exe tests\test_benchmark_runtime.py --models base medium
)

echo.
pause
