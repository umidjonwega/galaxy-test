"""
Custom DRF exception handler — barcha xatolar bir xil JSON formatda.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('pos_app')


def custom_exception_handler(exc, context):
    """
    Barcha xatolarni bir xil formatga keltiradi:
    {
        "error": "Xato xabari",
        "code": "error_code",
        "status": 400
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = response.data

        # DRF xatolarini tekis satrga aylantirish
        if isinstance(error_detail, dict):
            messages = []
            for field, errors in error_detail.items():
                if isinstance(errors, list):
                    messages.extend([str(e) for e in errors])
                else:
                    messages.append(str(errors))
            error_message = ' '.join(messages)
        elif isinstance(error_detail, list):
            error_message = ' '.join([str(e) for e in error_detail])
        else:
            error_message = str(error_detail)

        response.data = {
            'error': error_message,
            'code': getattr(exc, 'default_code', 'error'),
            'status': response.status_code,
        }

        if response.status_code >= 500:
            logger.error(f"Server xatosi: {exc}", exc_info=True)
        elif response.status_code >= 400:
            logger.warning(f"Client xatosi [{response.status_code}]: {error_message}")

    else:
        # Kutilmagan xatolar
        logger.exception(f"Kutilmagan xato: {exc}")
        response = Response(
            {'error': 'Ichki server xatosi yuz berdi.', 'code': 'internal_error', 'status': 500},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
