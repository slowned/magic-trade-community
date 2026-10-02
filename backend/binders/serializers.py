from rest_framework import serializers
from binders.models import Binder, WishlistCard
from cards.serializers import CardSerializer


class BinderSerializer(serializers.ModelSerializer):
    card_set = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    card_count = serializers.IntegerField(read_only=True)
    copy_count = serializers.SerializerMethodField()

    class Meta:
        model = Binder
        fields = ['id', 'name', 'is_public', 'user', 'card_count', 'copy_count', 'card_set']
        read_only_fields = ['user', 'card_set', 'card_count', 'copy_count']

    def _rows(self, obj):
        # Ordered by name so the grid doesn't reshuffle between reloads.
        return obj.bindercard_set.select_related('card').order_by('card__name', 'pk')

    def get_card_set(self, obj):
        """Each card with how many copies of it the binder holds.

        `quantity` is what tells a buyer they can ask for more than one, so it
        travels with the card rather than being flattened away.
        """
        cards = []
        for row in self._rows(obj):
            card = CardSerializer(row.card).data
            # `id` is the printing and repeats when the binder holds it in
            # more than one condition/language; this one is unique per row.
            card['binder_card_id'] = row.pk
            card['quantity'] = row.quantity
            card['foil'] = row.foil
            card['etched'] = row.etched
            card['condition'] = row.condition
            card['condition_display'] = row.get_condition_display()
            card['language'] = row.language
            card['language_display'] = row.get_language_display()
            cards.append(card)
        return cards

    def get_copy_count(self, obj):
        """Total copies, as opposed to `card_count`'s distinct cards."""
        return sum(row.quantity for row in self._rows(obj))


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
