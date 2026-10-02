from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0006_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='source',
            field=models.CharField(
                choices=[('binder', 'Binder'), ('auction', 'Subasta')],
                default='binder',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='price_ars',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
