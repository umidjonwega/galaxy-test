# ZAR POS — Omborxona va Savdo Tizimi.

## Tezkor ishga tushirish

### Windows
`start_windows.bat` faylini **ikki marta bosing**

### Mac / Linux
```bash
chmod +x start_mac.sh
./start_mac.sh
```

Brauzerda oching: **http://localhost:8000**

---

## Qo'lda o'rnatish

```bash
# 1. Virtual muhit
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env fayl
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux

# 4. Database
cd backend
python manage.py migrate

# 5. (Ixtiyoriy) Demo tovarlar
python manage.py shell -c "
from pos_app.models import Product
Product.objects.bulk_create([
    Product(name='iPhone 16 Pro 256GB',  barcode='1111111111111', price=25000000, quantity=5,  color='#0a84ff', category='Smartfonlar'),
    Product(name='Samsung S26 Ultra',    barcode='2222222222222', price=18500000, quantity=3,  color='#30d158', category='Smartfonlar'),
    Product(name='AirPods Pro 2',        barcode='3333333333333', price=4500000,  quantity=10, color='#64d2ff', category='Quloqchinlar'),
    Product(name='MacBook Air M3',       barcode='4444444444444', price=65000000, quantity=2,  color='#ff9f0a', category='Noutbuklar'),
    Product(name='iPad Pro 11',          barcode='5555555555555', price=35000000, quantity=4,  color='#bf5af2', category='Planshetlar'),
])
print('Demo tovarlar qoshildi!')
"

# 6. Serverni ishga tushirish
# Windows:
python -m waitress --host=127.0.0.1 --port=8000 --threads=4 backend.wsgi:application
# Mac/Linux:
gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 2
# Yoki (har qanday platforma):
python manage.py runserver
```

---

## Muammo: "hatolik chiqyapti"

**Eng ko'p uchraydigan xatolar:**

| Xato | Sabab | Yechim |
|------|-------|--------|
| 400 Bad Request | Noto'g'ri ma'lumot | Narx 0 dan katta bo'lsin |
| 400 barcode mavjud | Shtrix-kod takror | Boshqa kod kiriting |
| 500 Internal Error | Server muammosi | `logs/error.log` ni ko'ring |
| Internet xatosi | Tarmoq yo'q | `python manage.py runserver` ishlaydimi? |

---

## API

| Method | URL | Tavsif |
|--------|-----|--------|
| GET    | /api/products/ | Barcha tovarlar |
| GET    | /api/products/?search=... | Qidirish |
| POST   | /api/products/ | Yangi tovar qo'shish |
| PUT    | /api/products/{id}/ | Yangilash |
| DELETE | /api/products/{id}/ | O'chirish |
| POST   | /api/products/{id}/restock/ | Ombor to'ldirish |
| POST   | /api/sell/ | Sotish |
| GET    | /api/sales/ | Tarix |
| GET    | /api/currency/ | Valyuta kursi |

---

## Fayl tuzilmasi

```
ombor/
├── start_windows.bat     <- Windows uchun (ikki marta bosing)
├── start_mac.sh          <- Mac/Linux uchun
├── requirements.txt
├── .env.example          <- .env ga nusxa oling
└── backend/
    ├── manage.py
    ├── db.sqlite3        <- Ma'lumotlar bazasi
    ├── backend/
    │   ├── settings.py   <- Konfiguratsiya
    │   └── urls.py
    ├── pos_app/
    │   ├── models.py     <- Product, Sale, SaleItem
    │   ├── views.py      <- API
    │   ├── serializers.py
    │   └── services.py   <- Biznes logika
    └── frontend/
        └── index.html    <- Butun UI
```
