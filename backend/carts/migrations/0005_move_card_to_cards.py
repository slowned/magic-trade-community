from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0004_remove_cart_unique_together'),
        ('cards', '0001_initial'),
    ]

    # State-only: CartItem.card now points at cards.Card (see
    # binders.0010_move_card_to_cards) — same physical table, no DB change.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='cartitem',
                    name='card',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='cards.card'),
                ),
            ],
            database_operations=[],
        ),
    ]
