@echo off
title Transkrip Wawancara Lokal
echo ========================================================
echo       MEMULAI TRANSKRIP WAWANCARA LOKAL & MULTIBAHASA
echo ========================================================
cd /d "%~dp0"

REM Periksa apakah venv sudah ada
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [PERSIAPAN PERTAMA KALI] Virtual environment (venv) belum terpasang.
    echo Sistem akan menyiapkan lingkungan Python otomatis untuk komputer ini...
    echo.
    
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set PYCMD=py
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            set PYCMD=python
        ) else (
            echo [ERROR] Python belum terpasang di komputer Anda!
            echo Harap unduh dan pasang Python dari https://www.python.org/downloads/
            echo Pastikan centang "Add Python to PATH" saat instalasi.
            echo.
            pause
            exit /b
        )
    )

    echo Membuat Virtual Environment di folder venv...
    %PYCMD% -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Gagal membuat virtual environment.
        pause
        exit /b
    )

    echo Memasang pustaka yang dibutuhkan (requirements.txt)...
    echo Mohon tunggu sejenak, proses ini hanya satu kali di awal...
    call "venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Gagal memasang dependensi pustaka.
        pause
        exit /b
    )
    echo.
    echo [SUKSES] Instalasi otomatis selesai!
    echo.
)

call "venv\Scripts\activate.bat"
echo Menjalankan aplikasi di peramban (browser)...
python -m streamlit run app.py
pause

