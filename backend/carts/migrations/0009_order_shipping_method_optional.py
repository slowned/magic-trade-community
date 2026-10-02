from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0008_cartitemallocation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='shipping_method',
            field=models.CharField(
                blank=True,
                choices=[('door_to_door', 'Puerta a puerta'), ('branch_pickup', 'Retiro en sucursal')],
                default='',
                max_length=20,
            ),
        ),
    ]
