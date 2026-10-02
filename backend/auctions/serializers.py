from rest_framework import serializers

from auctions.models import (
    Auction,
    Bid,
    default_auction_window,
)
# `_card_defaults` is the single place Scryfall's payload is mapped onto Card;
# duplicating it here would drift the moment a field is added.
from binders.views import _card_defaults
from cards.models import Card
from cards.serializers import CardSerializer
from mtg_trade_community.scryfall import CardNotFound, Scryfall, ScryfallRequestError


class BidSerializer(serializers.ModelSerializer):
    """
    Public bid history. Deliberately omits `max_amount` — a bidder's ceiling
    is what makes proxy bidding work and must stay private.
    """
    bidder = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Bid
        fields = ['id', 'bidder', 'price_after', 'became_leader', 'created_at']


class AuctionSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    seller = serializers.SlugRelatedField(read_only=True, slug_field='username')
    current_leader = serializers.SlugRelatedField(read_only=True, slug_field='username')
    winner = serializers.SlugRelatedField(read_only=True, slug_field='username')

    display_title = serializers.CharField(read_only=True)
    display_image = serializers.CharField(read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    min_next_bid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    seconds_left = serializers.IntegerField(read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    reserve_met = serializers.BooleanField(read_only=True)
    has_reserve = serializers.SerializerMethodField()
    reserve_price = serializers.SerializerMethodField()

    cart_id = serializers.IntegerField(source='cart.id', read_only=True, allow_null=True)
    my_max_bid = serializers.SerializerMethodField()
    is_leading = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            'id', 'card', 'seller', 'title', 'display_title', 'description',
            'condition', 'condition_display', 'foil', 'etched',
            'image_url', 'display_image',
            'starting_price', 'min_increment', 'has_reserve', 'reserve_price', 'reserve_met',
            'starts_at', 'ends_at', 'status', 'status_display',
            'current_price', 'current_leader', 'bid_count', 'min_next_bid',
            'seconds_left', 'is_open',
            'winner', 'winning_amount', 'closed_at', 'cart_id',
            'my_max_bid', 'is_leading', 'created_at',
        ]

    def _user(self):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return user if (user and user.is_authenticated) else None

    @staticmethod
    def _amount(value):
        """Match DecimalField's string output for method-computed amounts."""
        return None if value is None else str(value)

    def get_has_reserve(self, obj):
        return obj.reserve_price is not None

    def get_reserve_price(self, obj):
        """Bidders see only whether the reserve was met; staff see the number."""
        user = self._user()
        return self._amount(obj.reserve_price) if (user and user.is_staff) else None

    def get_my_max_bid(self, obj):
        user = self._user()
        if not user:
            return None
        top = obj.bids.filter(bidder=user).order_by('-max_amount').first()
        return self._amount(top.max_amount) if top else None

    def get_is_leading(self, obj):
        user = self._user()
        return bool(user and obj.current_leader_id == user.pk)


class AuctionWriteSerializer(serializers.ModelSerializer):
    """
    Staff-facing create/update. Accepts either a Scryfall UUID (`card_id`) or
    a card name, fetching and caching the printing when it isn't in the DB yet.
    """
    card_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    card_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Auction
        fields = [
            'id', 'card_id', 'card_name', 'title', 'description',
            'condition', 'foil', 'etched', 'image_url',
            'starting_price', 'min_increment', 'reserve_price',
            'starts_at', 'ends_at',
        ]

    def validate(self, attrs):
        starts_at = attrs.get('starts_at', getattr(self.instance, 'starts_at', None))
        ends_at = attrs.get('ends_at', getattr(self.instance, 'ends_at', None))
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({'ends_at': 'El cierre debe ser posterior al inicio.'})

        for field in ('starting_price', 'min_increment'):
            value = attrs.get(field)
            if value is not None and value <= 0:
                raise serializers.ValidationError({field: 'Debe ser mayor a cero.'})

        reserve = attrs.get('reserve_price')
        start = attrs.get('starting_price', getattr(self.instance, 'starting_price', None))
        if reserve is not None and start is not None and reserve < start:
            raise serializers.ValidationError(
                {'reserve_price': 'El precio de reserva no puede ser menor al precio inicial.'}
            )

        card = self._resolve_card(attrs.pop('card_id', ''), attrs.pop('card_name', ''))
        if card:
            attrs['card'] = card
        elif not self.instance:
            raise serializers.ValidationError({'card_id': 'Indicá card_id o card_name.'})
        return attrs

    def _resolve_card(self, card_id, card_name):
        card_id = (card_id or '').strip()
        card_name = (card_name or '').strip()
        if not card_id and not card_name:
            return None

        if card_id:
            card = Card.objects.filter(id=card_id).first()
            if card:
                return card

        sf = Scryfall()
        try:
            data = sf.fetch_card_by_id(card_id) if card_id else sf.fetch_card_by_name(card_name)
        except CardNotFound:
            raise serializers.ValidationError({'card_id': 'No se encontró esa carta en Scryfall.'})
        except ScryfallRequestError:
            raise serializers.ValidationError({'card_id': 'Scryfall no respondió. Probá de nuevo.'})

        card, _ = Card.objects.update_or_create(id=data['id'], defaults=_card_defaults(data))
        return card


class DefaultWindowSerializer(serializers.Serializer):
    """The suggested Friday-to-Friday run used to prefill the create form."""
    starts_at = serializers.DateTimeField(read_only=True)
    ends_at = serializers.DateTimeField(read_only=True)

    @staticmethod
    def current():
        starts_at, ends_at = default_auction_window()
        return {'starts_at': starts_at, 'ends_at': ends_at}
