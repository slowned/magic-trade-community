from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from auctions.models import (
    STATUS_CANCELLED,
    STATUS_CLOSED,
    STATUS_LIVE,
    STATUS_SCHEDULED,
    Auction,
    BidError,
    settle_due_auctions,
)
from auctions.serializers import (
    AuctionSerializer,
    AuctionWriteSerializer,
    BidSerializer,
    DefaultWindowSerializer,
)
from mtg_trade_community.authentication import OptionalJWTAuthentication


class AuctionViewSet(ModelViewSet):
    """
    Auctions are read-only to the public, bid-able by any logged-in user, and
    created/managed by staff — that last restriction is the only thing standing
    between this and user-run auctions.
    """
    queryset = Auction.objects.select_related('card', 'seller', 'current_leader', 'winner', 'cart')
    authentication_classes = [OptionalJWTAuthentication]

    PUBLIC_ACTIONS = ('list', 'retrieve', 'bids')
    STAFF_ACTIONS = ('create', 'update', 'partial_update', 'destroy', 'close', 'cancel', 'default_window')

    def get_permissions(self):
        if self.action in self.PUBLIC_ACTIONS:
            return [AllowAny()]
        if self.action in self.STAFF_ACTIONS:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AuctionWriteSerializer
        return AuctionSerializer

    def get_queryset(self):
        # Every read path first brings the board up to date with the clock, so
        # a finished auction settles even with no worker running.
        settle_due_auctions()
        qs = super().get_queryset()

        if self.action != 'list':
            return qs

        requested = self.request.query_params.get('status', 'open').strip()
        if requested == 'open':
            qs = qs.filter(status__in=(STATUS_SCHEDULED, STATUS_LIVE))
        elif requested == 'live':
            qs = qs.filter(status=STATUS_LIVE)
        elif requested == 'upcoming':
            qs = qs.filter(status=STATUS_SCHEDULED)
        elif requested == 'closed':
            qs = qs.filter(status=STATUS_CLOSED).order_by('-closed_at')
        elif requested != 'all':
            qs = qs.filter(status=requested)

        search = self.request.query_params.get('q', '').strip()
        if search:
            qs = qs.filter(Q(card__name__icontains=search) | Q(title__icontains=search))

        if self.request.query_params.get('mine') and self.request.user.is_authenticated:
            qs = qs.filter(bids__bidder=self.request.user).distinct()

        return qs

    def _detail(self, auction, http_status=status.HTTP_200_OK):
        # An auction whose window already opened should come back `live`, not
        # `scheduled` — otherwise the client shows a stale state until the next read.
        auction.refresh_status()
        auction.refresh_from_db()
        return Response(
            AuctionSerializer(auction, context=self.get_serializer_context()).data,
            status=http_status,
        )

    def retrieve(self, request, *args, **kwargs):
        auction = self.get_object()
        auction.refresh_status()
        return self._detail(auction)

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self._detail(serializer.instance, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        auction = self.get_object()
        if auction.bid_count > 0:
            return Response(
                {'error': 'No se puede editar una subasta que ya tiene pujas.'},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = self.get_serializer(auction, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._detail(serializer.instance)

    def destroy(self, request, *args, **kwargs):
        auction = self.get_object()
        if auction.bid_count > 0:
            return Response(
                {'error': 'No se puede borrar una subasta con pujas. Cancelala en su lugar.'},
                status=status.HTTP_409_CONFLICT,
            )
        auction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='default-window')
    def default_window(self, request):
        """Suggested viernes-a-viernes window to prefill the create form."""
        return Response(DefaultWindowSerializer(DefaultWindowSerializer.current()).data)

    @action(detail=True, methods=['post'])
    def bid(self, request, pk=None):
        auction = self.get_object()
        try:
            auction.place_bid(request.user, request.data.get('max_amount'))
        except BidError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return self._detail(auction, status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        auction = self.get_object()
        history = auction.bids.select_related('bidder').all()[:50]
        return Response(BidSerializer(history, many=True).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Force an early close — settles at whatever the price is right now."""
        auction = self.get_object()
        if auction.status in (STATUS_CLOSED, STATUS_CANCELLED):
            return Response({'error': 'Esta subasta ya está cerrada.'}, status=status.HTTP_400_BAD_REQUEST)
        auction.ends_at = timezone.now()
        auction.save(update_fields=['ends_at', 'updated_at'])
        auction.settle()
        return self._detail(auction)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        auction = self.get_object()
        if auction.status in (STATUS_CLOSED, STATUS_CANCELLED):
            return Response({'error': 'Esta subasta ya está cerrada.'}, status=status.HTTP_400_BAD_REQUEST)
        auction.cancel()
        return self._detail(auction)
