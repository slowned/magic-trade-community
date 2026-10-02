from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cards.models import Card
from carts.models import Cart, CartItem, Message, Order, Rating
from carts.serializers import CartSerializer, MessageSerializer, OrderSerializer
from carts.stock import (
    StockUnavailable,
    available_quantity,
    deduct_for_checkout,
    is_binder_sale,
    restore_from_cancellation,
)
from mtg_trade_community.authentication import OptionalJWTAuthentication


class CartViewSet(GenericViewSet):
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def _buyer_qs(self):
        return Cart.objects.filter(
            buyer=self.request.user
        ).prefetch_related('items__card').select_related('seller', 'buyer', 'order')

    def _participant_cart(self, pk):
        """Return a cart where the current user is buyer OR seller."""
        return Cart.objects.filter(
            pk=pk
        ).filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        ).prefetch_related('items__card').select_related('seller', 'buyer', 'order').first()

    def list(self, request):
        return Response(CartSerializer(self._buyer_qs(), many=True).data)

    def retrieve(self, request, pk=None):
        cart = self._participant_cart(pk)
        if not cart:
            return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['get'], url_path='selling')
    def selling(self, request):
        """Carritos donde el usuario actual es el vendedor."""
        carts = Cart.objects.filter(
            seller=request.user
        ).prefetch_related('items__card').select_related('seller', 'buyer', 'order')
        return Response(CartSerializer(carts, many=True).data)

    @action(detail=False, methods=['post'], url_path='add-card')
    def add_card(self, request):
        seller_username = request.data.get('seller_username')
        card_id = request.data.get('card_id')
        quantity = max(1, int(request.data.get('quantity', 1)))

        if not seller_username or not card_id:
            return Response(
                {'error': 'seller_username y card_id son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if seller_username == request.user.username:
            return Response(
                {'error': 'No podés agregar tus propias cartas al carrito.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            seller = User.objects.get(username=seller_username)
        except User.DoesNotExist:
            return Response({'error': 'Vendedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            card = Card.objects.get(id=card_id)
        except Card.DoesNotExist:
            return Response({'error': 'Carta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        available = available_quantity(seller, card.id)
        if not available:
            return Response(
                {'error': 'El vendedor ya no tiene esa carta disponible.'},
                status=status.HTTP_409_CONFLICT
            )

        # Use the open (non-finalized) cart if one exists, else create a new one
        cart = Cart.objects.filter(
            buyer=request.user, seller=seller, is_finalized=False,
            source=Cart.SOURCE_BINDER,
        ).first()

        item = CartItem.objects.filter(cart=cart, card=card).first() if cart else None
        wanted = quantity + (item.quantity if item else 0)
        # Nothing is reserved until checkout, so this cap is only a courtesy:
        # it stops a buyer asking for copies the seller plainly doesn't have.
        # Checked before the cart is touched, so a rejection leaves no empty cart.
        if wanted > available:
            return Response(
                {
                    'error': f'El vendedor tiene {available} copia(s) disponible(s).',
                    'available': available,
                },
                status=status.HTTP_409_CONFLICT
            )

        if not cart:
            cart = Cart.objects.create(buyer=request.user, seller=seller)
        if not item:
            item = CartItem(cart=cart, card=card)
        item.quantity = wanted
        item.save()

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-card')
    def remove_card(self, request, pk=None):
        cart = self._buyer_qs().filter(pk=pk).first()
        if not cart:
            return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if cart.source == Cart.SOURCE_AUCTION:
            return Response(
                {'error': 'No se pueden quitar cartas de un carrito de subasta.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        CartItem.objects.filter(cart=cart, card_id=request.data.get('card_id')).delete()

        if not cart.items.exists():
            cart.delete()
            return Response({'deleted': True})

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        cart = self._buyer_qs().filter(pk=pk).first()
        if not cart:
            return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(cart, 'order'):
            return Response({'error': 'Este carrito ya tiene un checkout.'}, status=status.HTTP_400_BAD_REQUEST)

        # Shipping is settled in the order chat, so checkout no longer asks for
        # it. A client that still sends one has to send a real one.
        shipping_method = request.data.get('shipping_method') or ''
        if shipping_method and shipping_method not in ('door_to_door', 'branch_pickup'):
            return Response({'error': 'Método de envío inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        # First checkout wins. Locking the cart serializes double submissions of
        # this cart; `deduct_for_checkout` locks the seller's binder rows, so two
        # buyers racing for the same last copy can't both walk away with it.
        try:
            with transaction.atomic():
                locked = Cart.objects.select_for_update().get(pk=cart.pk)
                if Order.objects.filter(cart=locked).exists():
                    return Response(
                        {'error': 'Este carrito ya tiene un checkout.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if is_binder_sale(locked):
                    deduct_for_checkout(locked)

                Order.objects.create(
                    cart=locked,
                    shipping_method=shipping_method,
                    shipping_cost=request.data.get('shipping_cost') or None,
                    notes=request.data.get('notes', ''),
                )
                locked.is_finalized = True
                locked.save(update_fields=['is_finalized'])
        except StockUnavailable as exc:
            return Response(
                {
                    'error': 'Algunas cartas ya no están disponibles.',
                    'unavailable_cards': exc.unavailable,
                },
                status=status.HTTP_409_CONFLICT
            )

        cart = self._buyer_qs().get(pk=cart.pk)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='upload-payment')
    def upload_payment(self, request, pk=None):
        """Buyer uploads payment receipt (comprobante)."""
        cart = self._buyer_qs().filter(pk=pk).first()
        if not cart or not hasattr(cart, 'order'):
            return Response({'error': 'Orden no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        proof = request.FILES.get('payment_proof')
        if not proof:
            return Response({'error': 'No se encontró el archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        order = cart.order
        order.payment_proof = proof
        order.save()
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        cart = self._participant_cart(pk)
        if not cart or not hasattr(cart, 'order'):
            return Response({'error': 'Orden no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        valid = ('shipped', 'completed', 'cancelled')
        if new_status not in valid:
            return Response({'error': f'Estado inválido. Opciones: {valid}'}, status=status.HTTP_400_BAD_REQUEST)

        # Seller can mark as shipped; buyer can mark as completed or cancelled
        order = cart.order
        if new_status == 'shipped' and cart.seller != request.user:
            return Response({'error': 'Solo el vendedor puede marcar como enviado.'}, status=status.HTTP_403_FORBIDDEN)
        if new_status in ('completed', 'cancelled') and cart.buyer != request.user:
            return Response({'error': 'Solo el comprador puede marcar como completado o cancelado.'}, status=status.HTTP_403_FORBIDDEN)

        # Cancelling releases the copies the checkout took, back into the very
        # binders they came from. Auction carts never took any.
        with transaction.atomic():
            if new_status == 'cancelled' and order.status != 'cancelled' and is_binder_sale(cart):
                restore_from_cancellation(cart)
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])

        cart = self._participant_cart(pk)
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'], url_path='rate')
    def rate(self, request, pk=None):
        """Buyer rates the seller (0-10) once the order is completed."""
        cart = self._participant_cart(pk)
        if not cart or not hasattr(cart, 'order'):
            return Response({'error': 'Orden no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if cart.buyer != request.user:
            return Response(
                {'error': 'Solo el comprador puede puntuar al vendedor.'},
                status=status.HTTP_403_FORBIDDEN
            )

        order = cart.order
        if order.status != 'completed':
            return Response(
                {'error': 'Solo se puede puntuar un pedido completado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(order, 'rating'):
            return Response({'error': 'Este pedido ya fue puntuado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            score = int(request.data.get('score'))
        except (TypeError, ValueError):
            return Response({'error': 'score es requerido (0 a 10).'}, status=status.HTTP_400_BAD_REQUEST)
        if not 0 <= score <= 10:
            return Response({'error': 'La puntuación debe estar entre 0 y 10.'}, status=status.HTTP_400_BAD_REQUEST)

        Rating.objects.create(
            order=order,
            rater=request.user,
            ratee=cart.seller,
            score=score,
            comment=str(request.data.get('comment', '')).strip(),
        )
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        cart = self._participant_cart(pk)
        if not cart:
            return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            msgs = cart.messages.select_related('sender').all()
            return Response(MessageSerializer(msgs, many=True).data)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Mensaje vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        msg = Message.objects.create(cart=cart, sender=request.user, content=content)
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
