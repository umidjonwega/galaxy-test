@echo off
chcp 65001 >nul
echo.
echo  ============================================
echo    ZAR POS -- Windows da ishga tushirish
echo  ============================================
echo.

cd /d "%~dp0"

REM Python borligini tekshir
python --version >nul 2>&1
if errorlevel 1 (
    echo [XATO] Python topilmadi!
    echo https://python.org dan yuklab ornatib, PATH ga qoshing.
    pause
    exit /b 1
)

REM Virtual muhit yaratish
if not exist "venv" (
    echo [1/4] Virtual muhit yaratilmoqda...
    python -m venv venv
    if errorlevel 1 (
        echo [XATO] Virtual muhit yaratilmadi.
        pause
        exit /b 1
    )
)

REM Aktivlashtirish
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo [XATO] Virtual muhitni aktivlashtirib bolmadi.
    pause
    exit /b 1
)

REM .env fayl
if not exist ".env" (
    echo [OGOHLANTIRISH] .env fayl topilmadi, yaratilmoqda...
    copy .env.example .env >nul 2>&1
)

REM Kutubxonalar
echo [2/4] Kutubxonalar ornatilmoqda...
pip install -r requirements.txt -q --no-warn-script-location
if errorlevel 1 (
    echo [XATO] Kutubxonalar ornatilmadi. Internet bor mi?
    pause
    exit /b 1
)

REM Migratsiya
echo [3/4] Malumotlar bazasi tayyorlanmoqda...
cd backend
python manage.py migrate --noinput
if errorlevel 1 (
    echo [XATO] Migratsiya xatosi.
    pause
    exit /b 1
)
cd ..

REM Ishga tushirish
echo [4/4] Server ishga tushirilmoqda...
echo.
echo  ============================================
echo   Brauzerda oching: http://localhost:8000
echo   Toxtatish: bu oynani yoping yoki Ctrl+C
echo  ============================================
echo.

cd backend
python -m waitress --host=127.0.0.1 --port=8000 --threads=4 backend.wsgi:application

pause
