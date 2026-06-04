from rest_framework import serializers
from binders.models import Binder, Card, WishlistCard


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'id',
            'name',
            'set_name',
            'set_code',
            'color_identity',
            'type_line',
            'uri',
            'image_uri',
            'scryfall_uri',
            'price_usd',
            'price_usd_foil',
        ]


class BinderSerializer(serializers.ModelSerializer):
    card_set = CardSerializer(many=True, read_only=True)
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    card_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Binder
        fields = ['id', 'name', 'is_public', 'user', 'card_count', 'card_set']
        read_only_fields = ['user', 'card_set', 'card_count']


class AddCardsSerializer(serializers.Serializer):
    card_names = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False,
    )


class ImportMoxfieldSerializer(serializers.Serializer):
    csv_data = serializers.CharField()


class WishlistCardSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = WishlistCard
        fields = ['id', 'card', 'added_at']
