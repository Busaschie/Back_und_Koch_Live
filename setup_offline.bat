@echo off
cd /d "%~dp0"

echo Erstelle frische virtuelle Umgebung...
python -m venv .venv

echo Installiere Pakete offline aus dem wheels-Ordner...
.venv\Scripts\pip install --no-index --find-links=./wheels -r requirements.txt

echo Fertig! Du kannst die App jetzt mit start.bat starten.
pause