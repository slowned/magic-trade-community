from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from carts.models import CartItem, Order, Rating
from carts.serializers import RatingSerializer
from mtg_trade_community.authentication import OptionalJWTAuthentication
from users.models import UserProfile
from users.serializers import UserProfileSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [OptionalJWTAuthentication]

    def get_permissions(self):
        if self.action in ('create', 'public_profile'):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='public-profile/(?P<username>[^/]+)')
    def public_profile(self, request, username=None):
        """Public trust profile: rating average, successful trades and cards sold."""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        rating_stats = Rating.objects.filter(ratee=user).aggregate(
            avg=Avg('score'), count=Count('id'),
        )
        successful_trades = Order.objects.filter(
            status='completed', cart__seller=user,
        ).count() + Order.objects.filter(
            status='completed', cart__buyer=user,
        ).count()
        cards_sold = CartItem.objects.filter(
            cart__seller=user, cart__order__status='completed',
        ).aggregate(total=Sum('quantity'))['total'] or 0
        recent_ratings = Rating.objects.filter(ratee=user).select_related(
            'rater', 'ratee',
        ).order_by('-created_at')[:5]

        return Response({
            'username': user.username,
            'date_joined': user.date_joined,
            'rating_avg': round(rating_stats['avg'], 1) if rating_stats['avg'] is not None else None,
            'rating_count': rating_stats['count'],
            'successful_trades': successful_trades,
            'cards_sold': cards_sold,
            'binders': [
                {'id': b.id, 'name': b.name, 'card_count': b.card_set.count()}
                for b in user.binders.filter(is_public=True)
            ],
            'recent_ratings': RatingSerializer(recent_ratings, many=True).data,
        })

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['get', 'patch'], url_path='profile')
    def profile(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if request.method == 'GET':
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                **UserProfileSerializer(profile).data,
            })

        # PATCH — update profile + user fields
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user = request.user
            for field in ('first_name', 'last_name', 'email'):
                if field in request.data:
                    setattr(user, field, request.data[field])
            user.save()
            return Response({
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                **serializer.data,
            })
        return Response(serializer.errors, status=400)
