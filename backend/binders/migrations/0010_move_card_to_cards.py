from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('binders', '0009_alter_wishlistcard_added_at'),
        ('cards', '0001_initial'),
    ]

    # State-only: `Card` now lives in the `cards` app (see cards.0001_initial),
    # same physical `binders_card` table. Re-point the FKs that still say
    # 'binders.card' and drop Card from this app's state — no DB changes.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='bindercard',
                    name='card',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cards.card'),
                ),
                migrations.AlterField(
                    model_name='wishlistcard',
                    name='card',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cards.card'),
                ),
                migrations.DeleteModel(name='Card'),
            ],
            database_operations=[],
        ),
    ]
