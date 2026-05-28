"""
Business logic layer — production-ready:
- Django cache (Redis yoki LocMem) ishlatadi
- Atomik tranzaksiyalar bilan sotish
- To'liq loglash
- select_for_update() bilan race condition himoyasi
"""
import logging
import requests
from decimal import Decimal
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

from .models import Product, Sale, SaleItem

logger       = logging.getLogger('pos_app')
sales_logger = logging.getLogger('pos_app.sales')

CURRENCY_CACHE_KEY = 'currency:usd_uzs_rate'


# ── CURRENCY ───────────────────────────────────────────────────────────────

def get_usd_to_uzs_rate() -> int:
    """
    USD → UZS kursini olish.
    Django cache ishlatadi (TTL = settings.CURRENCY_CACHE_TTL).
    Muvaffaqiyatsiz bo'lsa — fallback rate qaytaradi.
    """
    cached = cache.get(CURRENCY_CACHE_KEY)
    if cached is not None:
        logger.debug(f"Valyuta kursi keshdan olindi: {cached}")
        return cached

    rate = _fetch_rate_from_api()
    ttl  = getattr(settings, 'CURRENCY_CACHE_TTL', 300)
    cache.set(CURRENCY_CACHE_KEY, rate, timeout=ttl)
    logger.info(f"Valyuta kursi yangilandi: {rate} UZS/USD (TTL={ttl}s)")
    return rate


def _fetch_rate_from_api() -> int:
    """Tashqi API dan kurs olish, muvaffaqiyatsiz bo'lsa fallback."""
    timeout  = getattr(settings, 'CURRENCY_API_TIMEOUT', 6)
    fallback = getattr(settings, 'CURRENCY_FALLBACK_RATE', 12800)

    apis = [
        ("O'zbekiston Markaziy Banki (CBU)", _fetch_cbu_api),
        ('open.er-api.com', _fetch_open_er_api),
    ]

    for api_name, fetch_fn in apis:
        try:
            rate = fetch_fn(timeout)
            if rate and rate > 1000:
                logger.info(f"Kurs {api_name} dan olindi: {rate}")
                return int(rate)
        except Exception as e:
            logger.warning(f"{api_name} muvaffaqiyatsiz: {e}")

    logger.warning(f"Barcha API lar muvaffaqiyatsiz. Fallback: {fallback}")
    return fallback


def _fetch_cbu_api(timeout: int) -> float:
    """
    O'zbekiston Markaziy Banki rasmiy API si.
    Endpoint: https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/
    Javob: [{"Ccy":"USD","Rate":"12950.00",...}]
    """
    r = requests.get(
        'https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/',
        timeout=timeout,
        headers={'Accept': 'application/json'}
    )
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and data:
        return float(data[0]['Rate'])
    raise ValueError("CBU API dan noto'g'ri javob keldi")


def _fetch_open_er_api(timeout: int) -> float:
    r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=timeout)
    r.raise_for_status()
    uzs = r.json()['rates'].get('UZS')
    if not uzs:
        raise ValueError("UZS kursi topilmadi")
    return uzs


def invalidate_currency_cache():
    """Valyuta keshini qo'lda tozalash."""
    cache.delete(CURRENCY_CACHE_KEY)
    logger.info("Valyuta keshi tozalandi.")


# ── SELL SERVICE ───────────────────────────────────────────────────────────

def process_sale(items_data: list) -> Sale:
    """
    Sotish tranzaksiyasi — atomic, thread-safe.

    Args:
        items_data: [{'product_id': int, 'barcode': str, 'quantity': int}, ...]

    Returns:
        Sale instance

    Raises:
        ValueError: Uzbek tilida xato xabari bilan
    """
    if not items_data:
        raise ValueError("Savat bo'sh. Kamida bitta mahsulot kiriting.")

    with transaction.atomic():
        resolved = _resolve_products(items_data)
        sale     = _create_sale_record(resolved)

    # Sales log (audit trail)
    _log_sale(sale, resolved)
    return sale


def _resolve_products(items_data: list) -> list:
    """
    Har bir item uchun mahsulotni topib, stok tekshiradi.
    select_for_update() bilan parallel so'rovlardan himoya.
    """
    resolved = []

    for item in items_data:
        product_id = item.get('product_id')
        barcode    = item.get('barcode')
        quantity   = item['quantity']

        # Mahsulotni topish
        try:
            qs = Product.objects.select_for_update()
            if product_id:
                product = qs.get(id=product_id)
            elif barcode:
                product = qs.get(barcode=barcode)
            else:
                raise ValueError("product_id yoki barcode talab qilinadi.")
        except Product.DoesNotExist:
            identifier = product_id or barcode
            raise ValueError(f"Mahsulot topilmadi: '{identifier}'")

        # Stok tekshiruvi
        if product.quantity < quantity:
            raise ValueError(
                f"'{product.name}' mahsulotidan yetarli stok yo'q. "
                f"Mavjud: {product.quantity} ta, So'ralgan: {quantity} ta."
            )

        resolved.append({
            'product':    product,
            'quantity':   quantity,
            'unit_price': product.price,
        })

    return resolved


def _create_sale_record(resolved: list) -> Sale:
    """Sale va SaleItem yozuvlarini yaratadi, stokni kamaytiradi."""
    total = sum(
        item['unit_price'] * Decimal(item['quantity'])
        for item in resolved
    )

    sale = Sale.objects.create(total_amount=total)

    for item in resolved:
        SaleItem.objects.create(
            sale        = sale,
            product     = item['product'],
            quantity    = item['quantity'],
            unit_price  = item['unit_price'],
            total_price = item['unit_price'] * Decimal(item['quantity']),
        )
        # Stokni kamaytirish (atomic ichida)
        item['product'].quantity -= item['quantity']
        item['product'].save(update_fields=['quantity', 'updated_at'])

    return sale


def _log_sale(sale: Sale, resolved: list):
    """Har bir sotuvni audit log fayliga yozish."""
    items_summary = ', '.join(
        f"{i['product'].name} x{i['quantity']} = {i['unit_price'] * i['quantity']} UZS"
        for i in resolved
    )
    sales_logger.info(
        f"SOTUV #{sale.id} | Jami: {sale.total_amount} UZS | "
        f"Mahsulotlar: [{items_summary}]"
    )


# ── STOCK SERVICE ──────────────────────────────────────────────────────────

def restock_product(product_id: int, add_quantity: int) -> Product:
    """
    Omborni to'ldirish.

    Args:
        product_id:   Mahsulot ID
        add_quantity: Qo'shilayotgan miqdor (musbat)

    Returns:
        Yangilangan Product instance
    """
    if add_quantity <= 0:
        raise ValueError("Qo'shiladigan miqdor musbat bo'lishi kerak.")

    with transaction.atomic():
        try:
            product = Product.objects.select_for_update().get(id=product_id)
        except Product.DoesNotExist:
            raise ValueError(f"Mahsulot topilmadi: ID={product_id}")

        old_qty = product.quantity
        product.quantity += add_quantity
        product.save(update_fields=['quantity', 'updated_at'])

    logger.info(
        f"OMBOR TO'LDIRILDI: {product.name} | "
        f"{old_qty} → {product.quantity} ta (+{add_quantity})"
    )
    return product
