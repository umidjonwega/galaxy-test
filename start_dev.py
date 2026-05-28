"""
ZAR POS — Universal Python Starter
Runs on Windows, Mac, Linux without shell scripts.
Usage: python start_dev.py
"""
import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
VENV = ROOT / "venv"

def run(cmd, **kw):
    print(f"  > {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, **kw)

def python_exe():
    """Find the correct python executable in venv or system."""
    candidates = [
        VENV / "Scripts" / "python.exe",   # Windows venv
        VENV / "bin" / "python",            # Mac/Linux venv
        VENV / "bin" / "python3",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return sys.executable  # fallback to current interpreter

def pip_exe():
    candidates = [
        VENV / "Scripts" / "pip.exe",
        VENV / "bin" / "pip",
        VENV / "bin" / "pip3",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None

def main():
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║         ZAR POS — Dev Server             ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    # 1. Create venv
    if not VENV.exists():
        print("[1/4] Virtual muhit yaratilmoqda...")
        run([sys.executable, "-m", "venv", str(VENV)], check=True)
    else:
        print("[1/4] Virtual muhit mavjud — OK")

    py = python_exe()
    pip = pip_exe() or f"{py} -m pip"

    # 2. Install deps
    print("[2/4] Kutubxonalar tekshirilmoqda...")
    req_file = str(ROOT / "requirements.txt")
    if isinstance(pip, str) and pip.endswith((".exe", "pip", "pip3")):
        run([pip, "install", "-r", req_file, "-q", "--no-warn-script-location"])
    else:
        run([py, "-m", "pip", "install", "-r", req_file, "-q"])

    # 3. .env
    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("[OGOHLANTIRISH] .env topilmadi. .env.example nusxa olinmoqda...")
        import shutil
        shutil.copy(str(env_example), str(env_file))

    # 4. Migrate
    print("[3/4] Malumotlar bazasi tayyorlanmoqda...")
    os.chdir(str(BACKEND))
    run([py, "manage.py", "migrate", "--noinput"], check=True)

    # 5. Start server
    print("[4/4] Server ishga tushirilmoqda...")
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  Brauzerda oching: http://localhost:8000 ║")
    print("  ║  To'xtatish uchun: Ctrl+C                ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    # Try waitress first (Windows-friendly), then gunicorn, then runserver
    try:
        import waitress
        from waitress import serve
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
        django.setup()
        from django.core.wsgi import get_wsgi_application
        app = get_wsgi_application()
        print("  Waitress server ishlamoqda...")
        serve(app, host="127.0.0.1", port=8000, threads=4)
    except ImportError:
        # Fallback to runserver
        run([py, "manage.py", "runserver", "127.0.0.1:8000"])

if __name__ == "__main__":
    main()
