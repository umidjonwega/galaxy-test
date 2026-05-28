import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Product(models.Model):
    name           = models.CharField(max_length=255)
    barcode        = models.CharField(max_length=100, unique=True, db_index=True, blank=True)
    price          = models.DecimalField(max_digits=15, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True)
    price_usd      = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    quantity       = models.PositiveIntegerField(default=0)
    color          = models.CharField(max_length=20, default='#30d158', blank=True)
    category       = models.CharField(max_length=100, blank=True, default='')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = 'AUTO-' + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.barcode})"


class Sale(models.Model):
    created_at   = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.id} - {self.created_at}"


class SaleItem(models.Model):
    sale       = models.ForeignKey(Sale, on_delete=models.CASCADE,  related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price= models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
