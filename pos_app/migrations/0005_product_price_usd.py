from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos_app', '0004_add_purchase_price_optional_barcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price_usd',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True),
        ),
    ]
