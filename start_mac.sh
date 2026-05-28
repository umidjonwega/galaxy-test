#!/bin/bash
set -e
cd "$(dirname "$0")"

echo ""
echo "  =========================================="
echo "    ZAR POS -- Mac/Linux ishga tushirish"
echo "  =========================================="
echo ""

# Python
if ! command -v python3 &>/dev/null; then
    echo "[XATO] python3 topilmadi."
    echo "Mac: brew install python3"
    echo "Ubuntu: sudo apt install python3 python3-venv"
    exit 1
fi

# Virtual muhit
if [ ! -d "venv" ]; then
    echo "[1/4] Virtual muhit yaratilmoqda..."
    python3 -m venv venv
fi
source venv/bin/activate

# .env
if [ ! -f ".env" ]; then
    echo "[OGOHLANTIRISH] .env yaratilmoqda..."
    cp .env.example .env
fi

# Kutubxonalar
echo "[2/4] Kutubxonalar ornatilmoqda..."
pip install -r requirements.txt -q

# Migratsiya
echo "[3/4] Malumotlar bazasi tayyorlanmoqda..."
cd backend
python manage.py migrate --noinput
cd ..

# Ishga tushirish
echo "[4/4] Server ishga tushirilmoqda..."
echo ""
echo "  =========================================="
echo "   Brauzerda oching: http://localhost:8000"
echo "   Toxtatish: Ctrl+C"
echo "  =========================================="
echo ""

cd backend
if python -c "import gunicorn" 2>/dev/null; then
    gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 60
elif python -c "import waitress" 2>/dev/null; then
    python -m waitress --host=127.0.0.1 --port=8000 backend.wsgi:application
else
    python manage.py runserver 127.0.0.1:8000
fi
