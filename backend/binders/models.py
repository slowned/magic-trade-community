from django.db import models
from django.contrib.auth.models import User


class Binder(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='binders'
    )
    name = models.CharField(max_length=255)
    # card_set (qs)

    def __str__(self):
        return f"Binder: {self.name} by {self.user.username}"


class Card(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    binders = models.ManyToManyField(Binder, through='BinderCard', blank=True)
    name = models.CharField(max_length=255)
    set_name = models.CharField(max_length=255)
    color_identity = models.CharField(max_length=255)

    # Tipo (creature, sorc, inst, planeswalker)
    uri = models.CharField(max_length=255)
    scryfall_uri = models.CharField(max_length=255)
    image_uri = models.URLField(max_length=255)
    # colors

    # TODO: agregar precio d cartas
    # ck_nm_price = models.DecimalField()
    # ck_sp_price = models.DecimalField()
    # ck_pl_price = models.DecimalField()
    # ck_dmg_price = models.DecimalField()

    def __str__(self):
        return f"{self.name}"


class BinderCard(models.Model):
    binder = models.ForeignKey(Binder, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    # TODO: agregar stado (NM, PL, DMG), eliminar quantity y unique_together
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('binder', 'card')

    def __str__(self):
        return f"{self.quantity}x {self.card.name} in {self.binder.name}"
