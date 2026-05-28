from django.urls import path
from . import views

urlpatterns = [
    path('products/',                views.ProductListCreateView.as_view()),
    path('products/<int:pk>/',       views.ProductDetailView.as_view()),
    path('products/<int:pk>/restock/', views.RestockView.as_view()),
    path('sell/',                    views.SellView.as_view()),
    path('sales/',                   views.SalesHistoryView.as_view()),
    path('sales/clear/',             views.ClearHistoryView.as_view()),
    path('sales/<int:pk>/delete/',   views.DeleteSaleView.as_view()),
    path('stats/',                   views.StatsView.as_view()),
    path('health/',                  views.HealthView.as_view()),
    path('currency/',                views.CurrencyView.as_view()),
    path('scan/<str:barcode>/',      views.ScanProductView.as_view()),
]
