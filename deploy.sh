#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  POS Tizim — Production Deploy Skripti
#  Ishlatish: chmod +x deploy.sh && ./deploy.sh
# ══════════════════════════════════════════════════════════════
set -e  # Xato bo'lsa to'xtat

APP_DIR="/var/www/pos_tizim"
VENV="$APP_DIR/venv"
BACKEND="$APP_DIR/backend"

echo "🚀 POS Tizim deploy boshlandi..."

# 1. Kod yangilash
echo "📥 Kod yuklanmoqda..."
cd "$APP_DIR"
git pull origin main

# 2. Virtual environment
echo "🐍 Virtual environment..."
python3 -m venv "$VENV" --upgrade-deps
source "$VENV/bin/activate"

# 3. Paketlar
echo "📦 Paketlar o'rnatilmoqda..."
pip install -r requirements.txt --quiet

# 4. Migratsiyalar
echo "🗄️  Ma'lumotlar bazasi yangilanmoqda..."
cd "$BACKEND"
python manage.py migrate --noinput

# 5. Statik fayllar
echo "📁 Statik fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput --clear

# 6. Log papkasi
mkdir -p "$BACKEND/logs"

# 7. Restart
echo "🔄 Servis qayta ishga tushirilmoqda..."
sudo systemctl restart pos_tizim
sudo systemctl reload nginx

# 8. Sog'liqni tekshirish
sleep 2
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/)
if [ "$STATUS" == "200" ]; then
    echo "✅ Deploy muvaffaqiyatli! Health check: OK"
else
    echo "❌ Health check muvaffaqiyatsiz! Status: $STATUS"
    sudo systemctl status pos_tizim --no-pager
    exit 1
fi

echo "🎉 POS Tizim ishga tushdi!"
