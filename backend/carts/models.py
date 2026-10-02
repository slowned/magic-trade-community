from django.core.validators import MaxValueValidator
from django.db import models
from django.contrib.auth.models import User

from cards.models import CONDITION_CHOICES, LANGUAGE_CHOICES, Card


class Cart(models.Model):
    SOURCE_BINDER = 'binder'
    SOURCE_AUCTION = 'auction'
    SOURCE_CHOICES = [
        (SOURCE_BINDER, 'Binder'),
        (SOURCE_AUCTION, 'Subasta'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts_as_seller')
    is_finalized = models.BooleanField(default=False)
    # Auction carts hold cards the seller never listed in a binder, so the
    # binder-availability checks in checkout don't apply to them.
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_BINDER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart: {self.buyer.username} ← {self.seller.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    card = models.ForeignKey(Card, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    # Unit price agreed outside Scryfall pricing (an auction's winning bid).
    # Null means "fall back to the card's USD price".
    price_ars = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('cart', 'card')

    def __str__(self):
        return f"{self.quantity}x {self.card.name} in cart {self.cart.id}"


class CartItemAllocation(models.Model):
    """Where each sold copy was taken from, recorded at checkout.

    A single item can draw from more than one of the seller's binders, so the
    deduction is stored per binder. It is what lets a cancelled order put the
    cards back exactly where they came from; `foil`/`etched`/`condition`/
    `language` are copied along because the `BinderCard` row they describe may
    be gone by then.
    """
    item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='allocations')
    binder = models.ForeignKey('binders.Binder', on_delete=models.CASCADE, related_name='allocations')
    quantity = models.PositiveIntegerField()
    foil = models.BooleanField(default=False)
    etched = models.BooleanField(default=False)
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, default='NM')
    language = models.CharField(max_length=3, choices=LANGUAGE_CHOICES, default='EN')

    def __str__(self):
        return f"{self.quantity}x {self.item.card.name} from {self.binder.name}"


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
    # Optional: checkout no longer asks how the cards travel. Buyer and seller
    # agree on it in the order chat, and it's recorded here only once they do.
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, blank=True, default='')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    payment_proof = models.FileField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.cart}"


class Rating(models.Model):
    """Buyer's trust rating (0-10) for the seller, one per completed order."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rating')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(10)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rater.username} → {self.ratee.username}: {self.score}/10"


class Message(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"
