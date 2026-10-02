from rest_framework import serializers
from cards.models import Card


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'id',
            'name',
            'set_name',
            'set_code',
            'collector_number',
            'color_identity',
            'type_line',
            'uri',
            'image_uri',
            'scryfall_uri',
            'price_usd',
            'price_usd_foil',
        ]
