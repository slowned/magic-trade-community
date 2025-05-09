from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from binders.models import Card


class CheckCardsView(APIView):
    def post(self, request):
        names = request.data.get('names', [])

        if not isinstance(names, list):
            return Response(
                {"error": "El campo 'names' debe ser una lista de nombres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar nombres exactos en la base de datos
        existing_cards = Card.objects.filter(
            name__in=names).values_list('name', flat=True)
        not_found = [name for name in names if name not in existing_cards]

        return Response({
            "existing_cards": list(existing_cards),
            "not_found": not_found
        })
