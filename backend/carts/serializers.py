from rest_framework import serializers
from carts.models import Cart, CartItem, Order, Message, Rating
from cards.serializers import CardSerializer


class RatingSerializer(serializers.ModelSerializer):
    rater = serializers.SlugRelatedField(read_only=True, slug_field='username')
    ratee = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Rating
        fields = ['id', 'rater', 'ratee', 'score', 'comment', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'card', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    shipping_method_display = serializers.CharField(source='get_shipping_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_proof_url = serializers.SerializerMethodField()
    rating = RatingSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_method', 'shipping_method_display',
            'shipping_cost', 'status', 'status_display', 'notes',
            'payment_proof_url', 'rating', 'created_at',
        ]

    def get_payment_proof_url(self, obj):
        if not obj.payment_proof:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.payment_proof.url)
        return obj.payment_proof.url


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    seller = serializers.SlugRelatedField(read_only=True, slug_field='username')
    buyer = serializers.SlugRelatedField(read_only=True, slug_field='username')
    item_count = serializers.SerializerMethodField()
    order = OrderSerializer(read_only=True)
    total_usd = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'buyer', 'seller', 'is_finalized',
            'created_at', 'item_count', 'total_usd', 'items', 'order',
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_total_usd(self, obj):
        total = sum(
            (item.card.price_usd or 0) * item.quantity
            for item in obj.items.all()
        )
        return float(total)
