from django.db import models
from django.contrib.auth.models import User


class Binder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='binders')
    name = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Binder: {self.name} by {self.user.username}"

    @property
    def card_count(self):
        return self.card_set.count()


class Card(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    binders = models.ManyToManyField(Binder, through='BinderCard', blank=True)
    name = models.CharField(max_length=255, db_index=True)
    set_name = models.CharField(max_length=255)
    set_code = models.CharField(max_length=10, blank=True, default='')
    color_identity = models.CharField(max_length=255)
    type_line = models.CharField(max_length=255, blank=True, default='')

    uri = models.CharField(max_length=512)
    scryfall_uri = models.CharField(max_length=512)
    image_uri = models.URLField(max_length=512, blank=True, default='')

    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    price_usd_foil = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    price_usd_etched = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    def __str__(self):
        return self.name


class BinderCard(models.Model):
    binder = models.ForeignKey(Binder, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    foil = models.BooleanField(default=False)
    etched = models.BooleanField(default=False)

    class Meta:
        unique_together = ('binder', 'card')

    def __str__(self):
        return f"{self.quantity}x {self.card.name} in {self.binder.name}"


class WishlistCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'card')

    def __str__(self):
        return f"{self.user.username} quiere {self.card.name}"
