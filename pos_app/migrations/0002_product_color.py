from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='color',
            field=models.CharField(
                blank=True,
                choices=[
                    ('#ef4444', 'Qizil'),
                    ('#f97316', "To'q sariq"),
                    ('#f59e0b', 'Sariq'),
                    ('#eab308', 'Limon'),
                    ('#84cc16', 'Yashil-sariq'),
                    ('#22c55e', 'Yashil'),
                    ('#10b981', 'Zangori-yashil'),
                    ('#14b8a6', 'Teal'),
                    ('#06b6d4', 'Moviy'),
                    ('#0ea5e9', "Ko'k"),
                    ('#3b82f6', 'Siniy'),
                    ('#6366f1', 'Indigo'),
                    ('#8b5cf6', 'Binafsha'),
                    ('#a855f7', "To'q binafsha"),
                    ('#d946ef', 'Pushti-binafsha'),
                    ('#ec4899', 'Pushti'),
                    ('#f43f5e', 'Qizil-pushti'),
                    ('#78716c', 'Kulrang-jigarrang'),
                    ('#6b7280', 'Kulrang'),
                    ('#0f172a', 'Qora'),
                    ('#7c3aed', "To'q binafsha 2"),
                    ('#0891b2', "To'q moviy"),
                    ('#059669', "To'q yashil"),
                    ('#b45309', 'Jigarrang'),
                ],
                default='#3b82f6',
                max_length=7,
            ),
        ),
    ]
