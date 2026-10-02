from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone

from cards.models import CONDITION_CHOICES, Card
from carts.models import Cart, CartItem, Message

# A bid landing this close to the end pushes the close time back by the same
# amount, so a last-second snipe always gives the room a chance to answer.
ANTI_SNIPE_WINDOW = timedelta(minutes=3)

# Auctions run on the local calendar even though the DB stores UTC.
AR_TZ = ZoneInfo('America/Argentina/Buenos_Aires')

# The usual cadence: open Friday evening, close the following Friday.
DEFAULT_OPEN_WEEKDAY = 4  # Monday is 0
DEFAULT_OPEN_TIME = time(21, 0)
DEFAULT_RUN_DAYS = 7

CENTS = Decimal('0.01')


class BidError(Exception):
    """A bid the auction rules reject — surfaced to the client as a 400."""


def default_auction_window(now=None):
    """
    Return (starts_at, ends_at) for the next Friday-to-Friday run.

    If it's Friday before 21:00 the window opens today; otherwise it rolls to
    the next Friday. Both values come back as aware UTC datetimes.
    """
    now_local = (now or timezone.now()).astimezone(AR_TZ)
    days_ahead = (DEFAULT_OPEN_WEEKDAY - now_local.weekday()) % 7
    opens_local = datetime.combine(
        now_local.date() + timedelta(days=days_ahead), DEFAULT_OPEN_TIME, tzinfo=AR_TZ
    )
    if opens_local <= now_local:
        opens_local += timedelta(days=7)
    return opens_local.astimezone(timezone.utc), (opens_local + timedelta(days=DEFAULT_RUN_DAYS)).astimezone(timezone.utc)


def to_amount(value, field='monto'):
    """Coerce user input to a positive 2-decimal amount, or raise BidError."""
    try:
        amount = Decimal(str(value)).quantize(CENTS)
    except (InvalidOperation, TypeError, ValueError):
        raise BidError(f'El {field} no es un número válido.')
    if amount <= 0:
        raise BidError(f'El {field} debe ser mayor a cero.')
    return amount


STATUS_SCHEDULED = 'scheduled'
STATUS_LIVE = 'live'
STATUS_CLOSED = 'closed'
STATUS_CANCELLED = 'cancelled'

STATUS_CHOICES = [
    (STATUS_SCHEDULED, 'Programada'),
    (STATUS_LIVE, 'En curso'),
    (STATUS_CLOSED, 'Cerrada'),
    (STATUS_CANCELLED, 'Cancelada'),
]


class Auction(models.Model):
    """
    A single-card auction with eBay-style proxy bidding, priced in ARS.

    Bidders submit the most they are willing to pay (`Bid.max_amount`); the
    auction only ever charges `current_price`, which climbs to one increment
    above the runner-up. `leader_max_amount` is the leader's hidden ceiling
    and must never be serialized to clients.

    For now auctions are created by staff (the platform is the seller); the
    `seller` FK is what will let users run their own later.
    """

    card = models.ForeignKey(Card, on_delete=models.PROTECT, related_name='auctions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions')

    title = models.CharField(max_length=255, blank=True, help_text='Vacío usa el nombre de la carta.')
    description = models.TextField(blank=True)
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, default='NM')
    foil = models.BooleanField(default=False)
    etched = models.BooleanField(default=False)
    image_url = models.URLField(max_length=512, blank=True, help_text='Vacío usa la imagen de Scryfall.')

    starting_price = models.DecimalField(max_digits=12, decimal_places=2)
    min_increment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('500.00'))
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED, db_index=True)

    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_leader = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leading_auctions'
    )
    leader_max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bid_count = models.PositiveIntegerField(default=0)

    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions'
    )
    winning_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    cart = models.OneToOneField(
        Cart, on_delete=models.SET_NULL, null=True, blank=True, related_name='auction'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ends_at', 'id']

    def __str__(self):
        return f"Subasta #{self.pk}: {self.display_title}"

    def save(self, *args, **kwargs):
        if self.current_price <= 0:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)

    # ── Derived display fields ──

    @property
    def display_title(self):
        return self.title or self.card.name

    @property
    def display_image(self):
        return self.image_url or self.card.image_uri

    @property
    def reserve_met(self):
        return self.reserve_price is None or self.current_price >= self.reserve_price

    @property
    def has_ended(self):
        return self.ends_at <= timezone.now()

    @property
    def seconds_left(self):
        if self.status in (STATUS_CLOSED, STATUS_CANCELLED):
            return 0
        return max(0, int((self.ends_at - timezone.now()).total_seconds()))

    @property
    def min_next_bid(self):
        """The smallest max_amount a new challenger can submit."""
        if self.bid_count == 0:
            return self.starting_price
        return self.current_price + self.min_increment

    @property
    def is_open(self):
        return self.status == STATUS_LIVE and not self.has_ended

    # ── Lifecycle ──

    def refresh_status(self):
        """
        Move the auction to whatever state the clock says it should be in.

        Called on every read path so an auction that ran out while nobody was
        looking still settles, with no worker process involved.
        """
        if self.status in (STATUS_CLOSED, STATUS_CANCELLED):
            return self.status

        now = timezone.now()
        if self.ends_at <= now:
            self.settle()
        elif self.status == STATUS_SCHEDULED and self.starts_at <= now:
            self.status = STATUS_LIVE
            self.save(update_fields=['status', 'updated_at'])
        return self.status

    @transaction.atomic
    def settle(self):
        """Close a finished auction and, if it sold, open the winner's cart."""
        auction = Auction.objects.select_for_update().get(pk=self.pk)
        if auction.status in (STATUS_CLOSED, STATUS_CANCELLED) or not auction.has_ended:
            self.refresh_from_db()
            return self

        auction.status = STATUS_CLOSED
        auction.closed_at = timezone.now()

        if auction.current_leader_id and auction.reserve_met:
            auction.winner_id = auction.current_leader_id
            auction.winning_amount = auction.current_price
            auction.cart = auction._open_settlement_cart()

        auction.save()
        self.refresh_from_db()
        return self

    def _open_settlement_cart(self):
        """
        Hand the win off to the existing order flow: a cart the winner checks
        out normally, so shipping, payment proof, chat and rating all work
        without an auction-specific pipeline.
        """
        cart = Cart.objects.create(buyer=self.winner, seller=self.seller, source=Cart.SOURCE_AUCTION)
        CartItem.objects.create(cart=cart, card=self.card, quantity=1, price_ars=self.winning_amount)
        Message.objects.create(
            cart=cart,
            sender=self.seller,
            content=(
                f'¡Ganaste la subasta de {self.display_title} por ${self.winning_amount}! '
                'Coordinemos el pago y el envío por acá.'
            ),
        )
        return cart

    @transaction.atomic
    def cancel(self):
        self.status = STATUS_CANCELLED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])
        return self

    # ── Bidding ──

    @transaction.atomic
    def place_bid(self, bidder, max_amount):
        """
        Register a proxy bid of `max_amount` for `bidder`.

        Returns the created Bid. Raises BidError with a message meant for the
        bidder when the auction rules reject it.
        """
        auction = Auction.objects.select_for_update().get(pk=self.pk)
        auction.refresh_status()

        if auction.status == STATUS_CANCELLED:
            raise BidError('Esta subasta fue cancelada.')
        if auction.status == STATUS_CLOSED:
            raise BidError('Esta subasta ya cerró.')
        if auction.status == STATUS_SCHEDULED:
            raise BidError('Esta subasta todavía no arrancó.')
        if bidder.pk == auction.seller_id:
            raise BidError('No podés pujar en tu propia subasta.')

        amount = to_amount(max_amount, 'monto')
        increment = auction.min_increment

        if auction.bid_count == 0:
            if amount < auction.starting_price:
                raise BidError(f'La primera puja debe ser de al menos ${auction.starting_price}.')
            auction.current_price = auction.starting_price
            auction.current_leader_id = bidder.pk
            auction.leader_max_amount = amount
            became_leader = True

        elif auction.current_leader_id == bidder.pk:
            # Already winning — the only useful move is raising your own ceiling,
            # which leaves the price alone.
            if amount <= auction.leader_max_amount:
                raise BidError(
                    f'Ya sos el mejor postor. Para subir tu máximo ofrecé más de ${auction.leader_max_amount}.'
                )
            auction.leader_max_amount = amount
            became_leader = True

        else:
            minimum = auction.current_price + increment
            if amount < minimum:
                raise BidError(f'La puja mínima es ${minimum}.')

            if amount > auction.leader_max_amount:
                # Challenger takes the lead, paying just enough to clear the
                # old ceiling — never their full maximum.
                auction.current_price = min(amount, auction.leader_max_amount + increment)
                auction.current_leader_id = bidder.pk
                auction.leader_max_amount = amount
                became_leader = True
            else:
                # Outbid on arrival: the standing proxy absorbs it and the
                # price climbs to meet the challenger. Ties keep the earlier bidder.
                auction.current_price = min(auction.leader_max_amount, amount + increment)
                became_leader = False

        auction.bid_count += 1

        now = timezone.now()
        if auction.ends_at - now <= ANTI_SNIPE_WINDOW:
            auction.ends_at = now + ANTI_SNIPE_WINDOW

        auction.save()

        bid = Bid.objects.create(
            auction=auction,
            bidder=bidder,
            max_amount=amount,
            price_after=auction.current_price,
            became_leader=became_leader,
        )
        self.refresh_from_db()
        return bid


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')

    # What the bidder committed to. Private: only ever exposed to its own
    # bidder, never in the public history.
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    # The auction's price once this bid was applied — the public number.
    price_after = models.DecimalField(max_digits=12, decimal_places=2)
    became_leader = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.bidder.username} → subasta #{self.auction_id}: ${self.price_after}"


def settle_due_auctions():
    """
    Bring every auction up to date with the clock.

    Safe to call from a request or from the `close_auctions` command; both
    take the same row locks.
    """
    now = timezone.now()
    opened = Auction.objects.filter(
        status=STATUS_SCHEDULED, starts_at__lte=now, ends_at__gt=now
    ).update(status=STATUS_LIVE)

    due = Auction.objects.filter(
        status__in=(STATUS_SCHEDULED, STATUS_LIVE), ends_at__lte=now
    )
    closed = 0
    for auction in due:
        auction.settle()
        closed += 1
    return opened, closed
