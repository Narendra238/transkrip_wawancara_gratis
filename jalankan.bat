@echo off
title Transkrip Wawancara Lokal
echo Menjalankan aplikasi Transkrip Wawancara di Virtual Environment...
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (venv) belum ditemukan.
    echo Harap jalankan: py -m venv venv
    pause
    exit /b
)

call "venv\Scripts\activate.bat"
python -m streamlit run app.py
pause
