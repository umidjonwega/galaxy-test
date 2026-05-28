"""
Production middleware:
- Har bir so'rovni loglash (vaqt, IP, method, URL, status, davomiyligi)
- Sekin so'rovlarni alohida ogohlantirish
- Sog'liqni tekshirish uchun /health/ endpoint
"""
import time
import logging

logger = logging.getLogger('pos_app')
SLOW_REQUEST_THRESHOLD_MS = 500  # 500ms dan sekin = ogohlantirish


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # So'rov boshlanishi
        start = time.monotonic()
        ip    = self._get_ip(request)

        response = self.get_response(request)

        # So'rov tugashi
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        status_code = response.status_code
        method      = request.method
        path        = request.get_full_path()

        msg = f"{method} {path} → {status_code} | {duration_ms}ms | {ip}"

        if status_code >= 500:
            logger.error(msg)
        elif status_code >= 400:
            logger.warning(msg)
        elif duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(f"SEKIN SO'ROV: {msg}")
        else:
            logger.info(msg)

        # Javobga performance header qo'shish (debug uchun)
        response['X-Response-Time'] = f"{duration_ms}ms"
        return response

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
