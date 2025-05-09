from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Cart, CartItem, BinderCard
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        cart = self.get_object()
        binder_card_id = request.data.get('binder_card_id')
        quantity = request.data.get('quantity', 1)

        # Find the BinderCard
        try:
            binder_card = BinderCard.objects.get(id=binder_card_id)
            # Check if CartItem already exists
            cart_item, created = CartItem.objects.get_or_create(cart=cart, binder_card=binder_card)
            cart_item.quantity += quantity
            cart_item.save()
            return Response({"status": "item added"}, status=status.HTTP_200_OK)
        except BinderCard.DoesNotExist:
            return Response({"error": "BinderCard not found"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='add-to-cart')
    def add_to_cart(self, request):
        buyer = request.user
        cart, created = Cart.objects.get_or_create(buyer=buyer, is_finalized=False)

        for item in request.data.get('items', []):
            binder_card_id = item['binder_card_id']
            quantity = item.get('quantity', 1)

            binder_card = BinderCard.objects.get(id=binder_card_id)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, binder_card=binder_card)
            cart_item.quantity = quantity
            cart_item.save()

        return Response({"status": "Cart updated"}, status=status.HTTP_200_OK)
