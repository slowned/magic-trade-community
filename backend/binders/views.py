import csv
import io

from django.db.models.functions import Lower
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from mtg_trade_community.authentication import OptionalJWTAuthentication

from binders.models import Binder, BinderCard, WishlistCard
from binders.serializers import (
    AddCardsSerializer,
    BinderSerializer,
    ImportMoxfieldSerializer,
    WishlistCardSerializer,
)
from cards.models import Card
from cards.serializers import CardSerializer
from mtg_trade_community.scryfall import CardNotFound, Scryfall, ScryfallRequestError


def _card_defaults(data):
    """Map a Scryfall card dict to Card model field defaults."""
    return {
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


def _fetch_or_get_cards(names):
    """
    Resolve a batch of card names to Card instances in as few Scryfall
    requests as possible.

    Returns (cards_by_name, not_found):
      - cards_by_name: dict of {name.strip().lower(): Card}.
      - not_found: list of the original names that couldn't be resolved,
        even with a fuzzy-match fallback.
    """
    wanted = {}
    for name in names:
        stripped = name.strip()
        if stripped:
            wanted.setdefault(stripped.lower(), stripped)

    cards_by_name = {}
    existing = Card.objects.annotate(name_lower=Lower('name')).filter(name_lower__in=wanted.keys())
    for card in existing:
        cards_by_name[card.name.lower()] = card

    missing = [orig for key, orig in wanted.items() if key not in cards_by_name]
    not_found = []
    if not missing:
        return cards_by_name, not_found

    sf = Scryfall()
    try:
        found, still_missing = sf.fetch_cards_by_names(missing)
    except ScryfallRequestError:
        return cards_by_name, missing

    for data in found.values():
        card, _ = Card.objects.update_or_create(id=data['id'], defaults=_card_defaults(data))
        cards_by_name[card.name.lower()] = card

    # A handful of stragglers (typos, alternate spellings) that the exact-match
    # collection endpoint couldn't resolve — worth a fuzzy lookup each, since
    # this is normally a short list rather than the whole batch.
    for name in still_missing:
        try:
            data = sf.fetch_card_by_name(name)
            card, _ = Card.objects.update_or_create(id=data['id'], defaults=_card_defaults(data))
            cards_by_name[name.lower()] = card
            cards_by_name[card.name.lower()] = card
        except (CardNotFound, ScryfallRequestError):
            not_found.append(name)

    return cards_by_name, not_found


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
                qs = qs.filter(bindercard__card__name__icontains=card_name).distinct()
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

        names = serializer.validated_data['card_names']
        cards_by_name, not_found = _fetch_or_get_cards(names)

        added = []
        for name in names:
            card = cards_by_name.get(name.strip().lower())
            if not card:
                continue
            bc, _ = BinderCard.objects.get_or_create(binder=binder, card=card, defaults={'quantity': 0})
            bc.quantity += 1
            bc.save()
            added.append(card.name)

        return Response({'added': added, 'not_found': not_found})

    @action(detail=True, methods=['post'], url_path='add-card-by-id')
    def add_card_by_id(self, request, pk=None):
        """
        Add a specific card printing by its Scryfall UUID.
        Fetches the card from Scryfall if it's not already in the DB.

        Body: { "card_id": "<scryfall-uuid>" }
        """
        from mtg_trade_community.scryfall import Scryfall, CardNotFound, ScryfallRequestError

        binder = self.get_object()
        self._assert_owner(binder)

        card_id = request.data.get('card_id', '').strip()
        if not card_id:
            return Response({'error': 'card_id requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        card = Card.objects.filter(id=card_id).first()
        if not card:
            try:
                data = Scryfall().fetch_card_by_id(card_id)
                card, _ = Card.objects.update_or_create(id=data['id'], defaults=_card_defaults(data))
            except CardNotFound:
                return Response({'error': 'Carta no encontrada en Scryfall.'}, status=status.HTTP_404_NOT_FOUND)
            except ScryfallRequestError as e:
                return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        bc, _ = BinderCard.objects.get_or_create(binder=binder, card=card, defaults={'quantity': 0})
        bc.quantity += 1
        bc.save()
        return Response({'added': card.name, 'card': CardSerializer(card).data})

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
        rows = []
        for row in reader:
            name = (row.get('Name') or row.get('name', '')).strip()
            if not name:
                continue
            try:
                quantity = int(row.get('Count') or row.get('count') or 1)
            except (ValueError, TypeError):
                quantity = 1
            foil = str(row.get('Foil', '')).strip().lower() in ('yes', 'true', '1', 'foil')
            rows.append((name, quantity, foil))

        cards_by_name, not_found = _fetch_or_get_cards([name for name, _, _ in rows])

        added = []
        for name, quantity, foil in rows:
            card = cards_by_name.get(name.lower())
            if not card:
                continue
            bc, _ = BinderCard.objects.get_or_create(binder=binder, card=card, defaults={'quantity': 0})
            bc.quantity += quantity
            bc.foil = bc.foil or foil
            bc.save()
            added.append(card.name)

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

        names = serializer.validated_data['card_names']
        cards_by_name, not_found = _fetch_or_get_cards(names)

        added = []
        for name in names:
            card = cards_by_name.get(name.strip().lower())
            if not card:
                continue
            WishlistCard.objects.get_or_create(user=request.user, card=card)
            added.append(card.name)

        return Response({'added': added, 'not_found': not_found})

    def destroy(self, request, pk=None):
        WishlistCard.objects.filter(user=request.user, card_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='matches')
    def matches(self, request):
        from collections import defaultdict

        card_ids = list(
            WishlistCard.objects.filter(user=request.user).values_list('card_id', flat=True)
        )
        if not card_ids:
            return Response([])

        binder_cards = (
            BinderCard.objects
            .filter(card_id__in=card_ids, binder__is_public=True)
            .exclude(binder__user=request.user)
            .select_related('card', 'binder', 'binder__user')
        )

        user_map = defaultdict(list)
        for bc in binder_cards:
            user_map[bc.binder.user.username].append({
                'id': bc.card.id,
                'name': bc.card.name,
                'image_uri': bc.card.image_uri,
                'price_usd': str(bc.card.price_usd) if bc.card.price_usd else None,
                'binder_id': bc.binder.id,
                'binder_name': bc.binder.name,
                'quantity': bc.quantity,
            })

        result = [
            {'username': username, 'match_count': len(cards), 'cards': cards}
            for username, cards in sorted(user_map.items(), key=lambda x: -len(x[1]))
        ]
        return Response(result)
