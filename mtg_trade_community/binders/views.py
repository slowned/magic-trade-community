from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

from rest_framework.viewsets import ModelViewSet

from binders.models import Binder, BinderCard, Card
from binders.serializers import AddCardsSerializer, BinderSerializer

from rest_framework.views import APIView


class CheckCardsView(APIView):
    def post(self, request):
        names = request.data.get('names', [])

        if not isinstance(names, list):
            return Response(
                {"error": "El campo 'names' debe ser una lista de nombres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar nombres exactos en la base de datos
        existing_cards = Card.objects.filter(name__in=names).values_list('name', flat=True)
        not_found = [name for name in names if name not in existing_cards]

        return Response({
            "existing_cards": list(existing_cards),
            "not_found": not_found
        })

class BinderViewSet(ModelViewSet):
    """
    API endpoint that allows binder to be viewed or edited.
    """
    queryset = Binder.objects.all()
    serializer_class = BinderSerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='add-cards')
    def add_card(self, request, pk=None):
        binder = self.get_object()
        serializer = AddCardsSerializer(data=request.data)

        if serializer.is_valid():
            cards_data = serializer.validated_data['cards']

            for card_data in cards_data:
                card_id = card_data['card_id']
                quantity = card_data.get('quantity', 1)

                card = Card.objects.get(id=card_id)

                if card:
                    binder_card, created = BinderCard.objects.get_or_create(
                        binder=binder,
                        card=card
                    )
                    binder_card.quantity += quantity
                    binder_card.save()

#             # cards_to_add = Card.objects.filter(id__in=card_ids)
#             cards_to_add = Card.objects.filter(name__in=card_names)

#             binder.card_set.add(*cards_to_add)
            return Response(
                {"status": "cards added"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='remove-cards')
    def remove_card(self, request, pk=None):
        binder = self.get_object()
        serializer = AddCardsSerializer(data=request.data)

        if serializer.is_valid():
            cards_data = serializer.validated_data['cards']

            for card_data in cards_data:
                card_id = card_data['card_id']
                quantity = card_data.get('quantity', 1)

                try:
                    binder_card = BinderCard.objects.get(binder=binder, card__id=card_id)
                    if binder_card.quantity > quantity:
                        binder_card.quantity -= quantity
                        binder_card.save()
                    else:
                        binder_card.delete()
                except BinderCard.DoesNotExist:
                    continue

            return Response(
                {"status": "cards removed"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
