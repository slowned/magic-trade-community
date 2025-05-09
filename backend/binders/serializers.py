from django.contrib.auth.models import User
from rest_framework import serializers

from binders.models import Binder, Card


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'id',
            'name',
            'color_identity',
            'uri',
            'image_uri',
            'scryfall_uri',
        ]


class BinderSerializer(serializers.ModelSerializer):
    card_set = CardSerializer(many=True, required=False)

    class Meta:
        model = Binder
        fields = ['id', 'name', 'user', 'card_set']


class AddCardsSerializer(serializers.Serializer):
    cards = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            help_text="Listado de cartas con nombres y cantidades",
        ),
        help_text="Lista de diccionarios {'card_name': 'nombre', 'quantity': n}"
    )

    def validate(self, data):
        card_ids = [card['card_id'] for card in data['cards']]
        missing_cards = [card_id for card_id in card_ids if not Card.objects.filter(id=card_id).exists()]
        if missing_cards:
            raise serializers.ValidationError(f"Cards with names {missing_cards} do not exist.")
        return data

    # modificar el update en lugar de crear uno aparte
    # def update(self, instance, validated_data):
    #     pass


# #TODO: Refactor agregar este serializer al patch de Binder
# class AddCardsSerializer(serializers.Serializer):
#     card_names = serializers.ListField(
#         child=serializers.CharField(),
#         allow_empty=False
#     )

#     def validate_card_ids(self, value):
#         # Verifica si las cartas existen en la base de datos
#         missing_cards = [
#             card_name for card_name in value
#             if not Card.objects.filter(name=card_name).exists()
#         ]
#         # crear missing cards
#         # llamado al card serializer
#         if missing_cards:
#             raise serializers.ValidationError(f"Cards with IDs {missing_cards} do not exist.")
#         return value

