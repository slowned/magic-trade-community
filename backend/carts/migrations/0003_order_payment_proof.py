from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0002_order_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_proof',
            field=models.FileField(blank=True, null=True, upload_to='receipts/'),
        ),
    ]
