from django.db import models

from django.contrib.auth.models import User


class Cart(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_finalized = models.BooleanField(default=False)  # Tracks if the cart is ready for purchase
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    binder_card = models.ForeignKey(BinderCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Quantity of the selected card

    class Meta:
        unique_together = ('cart', 'binder_card')
