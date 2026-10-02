import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cards', '0001_initial'),
        ('carts', '0007_cart_source_cartitem_price_ars'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Auction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Vacío usa el nombre de la carta.', max_length=255)),
                ('description', models.TextField(blank=True)),
                ('condition', models.CharField(choices=[('NM', 'Near Mint'), ('SP', 'Slightly Played'), ('MP', 'Moderately Played'), ('HP', 'Heavily Played'), ('DMG', 'Damaged')], default='NM', max_length=3)),
                ('foil', models.BooleanField(default=False)),
                ('etched', models.BooleanField(default=False)),
                ('image_url', models.URLField(blank=True, help_text='Vacío usa la imagen de Scryfall.', max_length=512)),
                ('starting_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('min_increment', models.DecimalField(decimal_places=2, default=Decimal('500.00'), max_digits=12)),
                ('reserve_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('scheduled', 'Programada'), ('live', 'En curso'), ('closed', 'Cerrada'), ('cancelled', 'Cancelada')], db_index=True, default='scheduled', max_length=20)),
                ('current_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('leader_max_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('bid_count', models.PositiveIntegerField(default=0)),
                ('winning_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='auctions', to='cards.card')),
                ('cart', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='auction', to='carts.cart')),
                ('current_leader', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leading_auctions', to=settings.AUTH_USER_MODEL)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auctions', to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='won_auctions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['ends_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('price_after', models.DecimalField(decimal_places=2, max_digits=12)),
                ('became_leader', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('auction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='auctions.auction')),
                ('bidder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]
