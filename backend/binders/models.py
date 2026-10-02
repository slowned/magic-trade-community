from django.db import models
from django.contrib.auth.models import User

from cards.models import CONDITION_CHOICES, LANGUAGE_CHOICES, Card


class Binder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='binders')
    name = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Binder: {self.name} by {self.user.username}"

    @property
    def card_count(self):
        return self.card_set.count()


class BinderCard(models.Model):
    binder = models.ForeignKey(Binder, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    foil = models.BooleanField(default=False)
    etched = models.BooleanField(default=False)
    # Condition and language belong to the seller's physical copy, not to the
    # printing, so they live here rather than on Card. They are part of the
    # row's identity: 2 NM English and 1 SP Spanish copies of the same printing
    # are two rows, each with its own quantity.
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, default='NM')
    language = models.CharField(max_length=3, choices=LANGUAGE_CHOICES, default='EN')

    class Meta:
        unique_together = ('binder', 'card', 'condition', 'language')

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
