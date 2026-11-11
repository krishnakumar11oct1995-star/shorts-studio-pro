@echo off
title Roblox YouTube Shorts Studio (RTX 3050 GPU)
color 0b

echo =======================================================
echo   Roblox YouTube Shorts Studio (GPU Edition)
echo   Target GPU: NVIDIA GeForce RTX 3050 (4GB)
echo =======================================================
echo.

if not exist venv (
    echo [!] Virtual environment not found. Creating venv...
    python -m venv venv
    call .\venv\Scripts\activate.bat
    echo [*] Installing dependencies...
    pip install -r requirements.txt
) else (
    call .\venv\Scripts\activate.bat
)

echo [*] Starting Web Studio on http://127.0.0.1:7860 ...
python app.py
pause
