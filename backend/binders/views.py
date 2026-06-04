import csv
import io
import time

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from mtg_trade_community.authentication import OptionalJWTAuthentication

from binders.models import Binder, BinderCard, Card, WishlistCard
from binders.serializers import (
    AddCardsSerializer,
    BinderSerializer,
    CardSerializer,
    ImportMoxfieldSerializer,
    WishlistCardSerializer,
)
from mtg_trade_community.scryfall import CardNotFound, Scryfall, ScryfallRequestError


def _fetch_or_get_card(name):
    """Return (Card, None) or (None, name) if not found."""
    card = Card.objects.filter(name__iexact=name).first()
    if card:
        return card, None
    try:
        sf = Scryfall()
        data = sf.fetch_card_by_name(name)
        card, _ = Card.objects.update_or_create(
            id=data['id'],
            defaults={
                'name': data['name'],
                'set_name': data.get('set_name', ''),
                'set_code': data.get('set', ''),
                'color_identity': ','.join(data.get('color_identity', [])),
                'type_line': data.get('type_line', ''),
                'uri': data.get('uri', ''),
                'scryfall_uri': data.get('scryfall_uri', ''),
                'image_uri': data.get('image_uri', ''),
                'price_usd': data.get('prices', {}).get('usd') or None,
                'price_usd_foil': data.get('prices', {}).get('usd_foil') or None,
                'price_usd_etched': data.get('prices', {}).get('usd_etched') or None,
            }
        )
        return card, None
    except (CardNotFound, ScryfallRequestError):
        return None, name


class BinderViewSet(ModelViewSet):
    queryset = Binder.objects.all().select_related('user')
    serializer_class = BinderSerializer
    authentication_classes = [OptionalJWTAuthentication]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            qs = qs.filter(is_public=True)
            card_name = self.request.query_params.get('card_name', '').strip()
            if card_name:
                qs = qs.filter(card_set__name__icontains=card_name).distinct()
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _assert_owner(self, binder):
        if binder.user != self.request.user:
            raise PermissionDenied('No tenés permiso para modificar este binder.')

    def update(self, request, *args, **kwargs):
        self._assert_owner(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._assert_owner(self.get_object())
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='my-binders')
    def my_binders(self, request):
        binders = Binder.objects.filter(user=request.user).select_related('user')
        return Response(BinderSerializer(binders, many=True).data)

    @action(detail=True, methods=['post'], url_path='add-cards')
    def add_cards(self, request, pk=None):
        binder = self.get_object()
        self._assert_owner(binder)

        serializer = AddCardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        added, not_found = [], []
        for name in serializer.validated_data['card_names']:
            card, err = _fetch_or_get_card(name.strip())
            if err:
                not_found.append(err)
                continue
            bc, _ = BinderCard.objects.get_or_create(binder=binder, card=card)
            bc.quantity += 1
            bc.save()
            added.append(card.name)
            time.sleep(0.05)

        return Response({'added': added, 'not_found': not_found})

    @action(detail=True, methods=['post'], url_path='import-moxfield')
    def import_moxfield(self, request, pk=None):
        """
        Importa CSV exportado desde Moxfield:
          Count,Name,Edition,Condition,Language,Foil,Collector Number
        """
        binder = self.get_object()
        self._assert_owner(binder)

        serializer = ImportMoxfieldSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        reader = csv.DictReader(io.StringIO(serializer.validated_data['csv_data']))
        added, not_found = [], []

        for row in reader:
            name = (row.get('Name') or row.get('name', '')).strip()
            if not name:
                continue
            try:
                quantity = int(row.get('Count') or row.get('count') or 1)
            except (ValueError, TypeError):
                quantity = 1
            foil = str(row.get('Foil', '')).strip().lower() in ('yes', 'true', '1', 'foil')

            card, err = _fetch_or_get_card(name)
            if err:
                not_found.append(err)
                continue
            bc, _ = BinderCard.objects.get_or_create(binder=binder, card=card)
            bc.quantity += quantity
            bc.foil = bc.foil or foil
            bc.save()
            added.append(card.name)
            time.sleep(0.05)

        return Response({'added': added, 'not_found': not_found})

    @action(detail=True, methods=['post'], url_path='remove-cards')
    def remove_cards(self, request, pk=None):
        binder = self.get_object()
        self._assert_owner(binder)

        serializer = AddCardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        removed = []
        for name in serializer.validated_data['card_names']:
            try:
                bc = BinderCard.objects.get(binder=binder, card__name__iexact=name.strip())
                if bc.quantity > 1:
                    bc.quantity -= 1
                    bc.save()
                else:
                    bc.delete()
                removed.append(name)
            except BinderCard.DoesNotExist:
                continue

        return Response({'removed': removed})


class WishlistViewSet(GenericViewSet):
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistCardSerializer

    def get_queryset(self):
        return WishlistCard.objects.filter(
            user=self.request.user
        ).select_related('card').order_by('-added_at')

    def list(self, request):
        return Response(WishlistCardSerializer(self.get_queryset(), many=True).data)

    def create(self, request):
        serializer = AddCardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        added, not_found = [], []
        for name in serializer.validated_data['card_names']:
            card, err = _fetch_or_get_card(name.strip())
            if err:
                not_found.append(err)
                continue
            WishlistCard.objects.get_or_create(user=request.user, card=card)
            added.append(card.name)
            time.sleep(0.05)

        return Response({'added': added, 'not_found': not_found})

    def destroy(self, request, pk=None):
        WishlistCard.objects.filter(user=request.user, card_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
