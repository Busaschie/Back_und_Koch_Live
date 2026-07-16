@echo off
echo ===================================================
echo Starte Applikations-Infrastruktur...
echo ===================================================

:: Wechselt automatisch auf das richtige Laufwerk und in den Ordner dieser BAT-Datei
cd /d "%~dp0"

:: Pfade im VENV absolut definieren
set VENV_PYTHON="%~dp0.venv\Scripts\python.exe"
set PYTHONPATH=%CD%

:: 1. FastAPI Backend im Hintergrund starten
echo [BACKEND] Starte FastAPI Backend...
start "FastAPI_Backend" /b %VENV_PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8000

:: Kurz warten, bis das Backend bereit ist
timeout /t 3 /nobreak >nul

:: 2. Streamlit Frontend in einem stabilen Fenster starten
echo [FRONTEND] Starte Streamlit Frontend...
start "Streamlit_Frontend" cmd /k %VENV_PYTHON% -m streamlit run app.py --server.port 8501

echo ===================================================
echo Startbefehle wurden ausgefuehrt!
echo Schliessen Sie dieses Hauptfenster nicht.
echo ===================================================
pause
