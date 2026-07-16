import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    app_file = root / "app.py"  # weil app.py im gleichen Ordner wie main.py liegt

    print("main.py dir:", root)
    print("app exists:", app_file.exists(), app_file)

    if not app_file.exists():
        raise FileNotFoundError(f"Streamlit-App nicht gefunden: {app_file}")

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_file)],
        check=True
    )

if __name__ == "__main__":
    main()