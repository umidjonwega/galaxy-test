from rest_framework import serializers
from .models import Product, Sale, SaleItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ['id', 'name', 'barcode', 'price', 'price_usd', 'purchase_price',
                  'quantity', 'color', 'category', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_barcode(self, value):
        return (value or '').strip()

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Miqdor manfiy bo'lmasin.")
        return value

    def validate_color(self, value):
        v = (value or '#30d158').strip()
        if not v.startswith('#'):
            v = '#' + v
        return v[:20]


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model  = SaleItem
        fields = ['id', 'product_name', 'quantity', 'unit_price', 'total_price']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Sale
        fields = ['id', 'created_at', 'total_amount', 'items']


class SaleItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False)
    barcode    = serializers.CharField(required=False)
    quantity   = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if not data.get('product_id') and not data.get('barcode'):
            raise serializers.ValidationError(
                "product_id yoki barcode talab qilinadi."
            )
        return data


class SellInputSerializer(serializers.Serializer):
    items = SaleItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Savat bo'sh.")
        return value


class SalesHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    profit       = serializers.SerializerMethodField()

    class Meta:
        model  = SaleItem
        fields = ['product_name', 'quantity', 'unit_price', 'total_price', 'profit']

    def get_profit(self, obj):
        return str(obj.total_price - obj.product.purchase_price * obj.quantity)

    def to_representation(self, instance):
        return {
            'id':           instance.sale.id,
            'product_name': instance.product.name,
            'quantity':     instance.quantity,
            'unit_price':   str(instance.unit_price),
            'total_price':  str(instance.total_price),
            'profit':       str(instance.total_price - instance.product.purchase_price * instance.quantity),
            'date':         instance.sale.created_at.strftime('%Y-%m-%dT%H:%M:%S'),
        }
