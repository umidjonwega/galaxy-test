"""
API Views — production-ready:
- Throttling (rate limiting)
- Django cache
- Structured logging
- Health check endpoint
- Consistent JSON responses
"""
import logging
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser

from .models import Product, Sale, SaleItem
from .serializers import (
    ProductSerializer,
    SaleSerializer,
    SellInputSerializer,
    SalesHistorySerializer,
)
from .services import (
    get_usd_to_uzs_rate,
    process_sale,
    restock_product,
    invalidate_currency_cache,
)

logger = logging.getLogger('pos_app')

# ── CUSTOM THROTTLE ────────────────────────────────────────

class SellThrottle(AnonRateThrottle):
    scope = 'sell'


# ── HELPERS ────────────────────────────────────────────────

def ok(data, status_code=status.HTTP_200_OK):
    return Response(data, status=status_code)

def err(message, status_code=status.HTTP_400_BAD_REQUEST, code='error'):
    return Response({'error': message, 'code': code, 'status': status_code}, status=status_code)


# ── PRODUCTS ───────────────────────────────────────────────

class ProductListCreateView(APIView):

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        qs = Product.objects.all()
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(barcode__icontains=search)
            qs = qs.distinct()

        serializer = ProductSerializer(qs.order_by('name'), many=True)
        return ok(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        product = serializer.save()
        logger.info(f"Yangi mahsulot: {product.name} | barcode={product.barcode}")
        return ok(ProductSerializer(product).data, status.HTTP_201_CREATED)


class ProductDetailView(APIView):

    def _get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return err(f"Mahsulot topilmadi: ID={pk}", status.HTTP_404_NOT_FOUND, 'not_found')
        return ok(ProductSerializer(product).data)

    def put(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return err(f"Mahsulot topilmadi: ID={pk}", status.HTTP_404_NOT_FOUND, 'not_found')

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if not serializer.is_valid():
            return err(serializer.errors)

        updated = serializer.save()
        logger.info(f"Mahsulot yangilandi: {updated.name} | ID={pk}")
        return ok(ProductSerializer(updated).data)

    def delete(self, request, pk):
        from django.db.models import ProtectedError
        product = self._get_product(pk)
        if not product:
            return err(f"Mahsulot topilmadi: ID={pk}", status.HTTP_404_NOT_FOUND, 'not_found')
        name = product.name
        try:
            product.delete()
        except ProtectedError:
            return err(
                f"'{name}' mahsulotini o'chirib bo'lmaydi — sotuvlar tarixida mavjud.",
                status.HTTP_409_CONFLICT,
                'protected'
            )
        logger.info(f"Mahsulot o'chirildi: {name} | ID={pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── SCAN ───────────────────────────────────────────────────

class ScanProductView(APIView):

    def get(self, request, barcode):
        barcode = barcode.strip()
        # Short cache for repeated scans (10s)
        cache_key = f'scan:{barcode}'
        cached = cache.get(cache_key)
        if cached:
            return ok(cached)

        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            return err(
                f"Shtrix-kod topilmadi: '{barcode}'",
                status.HTTP_404_NOT_FOUND,
                'not_found'
            )

        data = ProductSerializer(product).data
        cache.set(cache_key, data, timeout=10)
        return ok(data)


# ── SELL ───────────────────────────────────────────────────

class SellView(APIView):
    throttle_classes = [SellThrottle]

    def post(self, request):
        serializer = SellInputSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)

        try:
            sale = process_sale(serializer.validated_data['items'])
        except ValueError as e:
            return err(str(e), status.HTTP_400_BAD_REQUEST, 'stock_error')

        # Scan cache va stats cache ni tozalash (stok o'zgardi)
        cache.delete('stats:summary')
        for item in serializer.validated_data['items']:
            bc = item.get('barcode')
            if bc:
                cache.delete(f'scan:{bc}')

        return ok(SaleSerializer(sale).data, status.HTTP_201_CREATED)


# ── SALES HISTORY ───────────────────────────────────────────

class SalesHistoryView(APIView):

    def get(self, request):
        try:
            page_size = max(1, min(500, int(request.query_params.get('page_size', 100))))
            page      = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            return err("page va page_size musbat son bo'lishi kerak.")

        offset = (page - 1) * page_size
        qs     = SaleItem.objects.select_related('product', 'sale').order_by('-sale__created_at')
        total  = qs.count()
        items  = qs[offset:offset + page_size]

        return ok({
            'total':     total,
            'page':      page,
            'page_size': page_size,
            'pages':     (total + page_size - 1) // page_size,
            'results':   SalesHistorySerializer(items, many=True).data,
        })


# ── CURRENCY ───────────────────────────────────────────────

class CurrencyView(APIView):

    def get(self, request):
        rate = get_usd_to_uzs_rate()
        return ok({'rate': rate, 'currency': 'USD/UZS', 'source': 'cache_or_api'})

    def post(self, request):
        """Keshni qo'lda tozalash (admin uchun)."""
        invalidate_currency_cache()
        rate = get_usd_to_uzs_rate()
        return ok({'rate': rate, 'message': "Valyuta kursi yangilandi."})


# ── RESTOCK ────────────────────────────────────────────────

class RestockView(APIView):

    def post(self, request, pk):
        add_qty = request.data.get('add_quantity')
        if add_qty is None:
            return err("add_quantity maydoni talab qilinadi.")
        try:
            add_qty = int(add_qty)
        except (ValueError, TypeError):
            return err("add_quantity butun son bo'lishi kerak.")

        try:
            product = restock_product(pk, add_qty)
        except ValueError as e:
            return err(str(e))

        return ok(ProductSerializer(product).data)


# ── HEALTH CHECK ───────────────────────────────────────────

class HealthView(APIView):
    """
    Monitoring uchun: /api/health/
    Kubernetes, Docker, uptime robots tomonidan tekshirilishi mumkin.
    """

    def get(self, request):
        checks = {}
        overall_ok = True

        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = {'status': 'ok'}
        except Exception as e:
            checks['database'] = {'status': 'error', 'detail': str(e)}
            overall_ok = False

        # Cache
        try:
            cache.set('health_check', 'ok', timeout=5)
            val = cache.get('health_check')
            checks['cache'] = {'status': 'ok' if val == 'ok' else 'error'}
        except Exception as e:
            checks['cache'] = {'status': 'error', 'detail': str(e)}
            overall_ok = False

        # App stats
        try:
            checks['stats'] = {
                'products': Product.objects.count(),
                'sales':    Sale.objects.count(),
            }
        except Exception:
            pass

        http_status = status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({
            'status':    'ok' if overall_ok else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'checks':    checks,
        }, status=http_status)


# ── STATS SUMMARY ──────────────────────────────────────────

class StatsView(APIView):
    """Dashboard uchun qisqacha statistika: /api/stats/"""

    def get(self, request):
        from django.db.models import Sum, Count
        cache_key = 'stats:summary'
        cached    = cache.get(cache_key)
        if cached:
            return ok(cached)

        products_qs = Product.objects.all()
        sales_qs    = SaleItem.objects.select_related('sale')

        data = {
            'products': {
                'total':    products_qs.count(),
                'in_stock': products_qs.filter(quantity__gt=0).count(),
                'low':      products_qs.filter(quantity__gt=0, quantity__lte=5).count(),
                'out':      products_qs.filter(quantity=0).count(),
            },
            'sales': {
                'total_transactions': Sale.objects.count(),
                'total_items_sold':   sales_qs.aggregate(s=Sum('quantity'))['s'] or 0,
                'total_revenue':      str(sales_qs.aggregate(s=Sum('total_price'))['s'] or 0),
            },
        }

        cache.set(cache_key, data, timeout=60)
        return ok(data)


# ── CLEAR HISTORY ──────────────────────────────────────────
class ClearHistoryView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def delete(self, request):
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        return Response({'ok': True, 'message': 'Tarix tozalandi.'})


# ── DELETE SINGLE SALE ─────────────────────────────────────
class DeleteSaleView(APIView):
    def delete(self, request, pk):
        try:
            sale = Sale.objects.get(pk=pk)
            # related_name='items' (saleitem_set emas!), CASCADE avtomatik o'chiradi
            sale.items.all().delete()
            sale.delete()
            return Response({'ok': True})
        except Sale.DoesNotExist:
            return err("Sotuv topilmadi", status.HTTP_404_NOT_FOUND)
