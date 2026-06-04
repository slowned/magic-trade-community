from django.db import models
from django.contrib.auth.models import User

from binders.models import Card


class Cart(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts_as_seller')
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart: {self.buyer.username} ← {self.seller.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    card = models.ForeignKey(Card, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'card')

    def __str__(self):
        return f"{self.quantity}x {self.card.name} in cart {self.cart.id}"


SHIPPING_CHOICES = [
    ('door_to_door', 'Puerta a puerta'),
    ('branch_pickup', 'Retiro en sucursal'),
]

ORDER_STATUS_CHOICES = [
    ('pending', 'Pendiente'),
    ('shipped', 'Enviado'),
    ('completed', 'Completado'),
    ('cancelled', 'Cancelado'),
]


class Order(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='order')
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    payment_proof = models.FileField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.cart}"


class Message(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"
