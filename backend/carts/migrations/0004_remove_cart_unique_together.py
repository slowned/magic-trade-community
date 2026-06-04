from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0003_order_payment_proof'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cart',
            unique_together=set(),
        ),
    ]
