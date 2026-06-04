from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from mtg_trade_community.authentication import OptionalJWTAuthentication
from users.models import UserProfile
from users.serializers import UserProfileSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [OptionalJWTAuthentication]

    def get_permissions(self):
        if self.action in ('create', 'login'):
            return [AllowAny()]
        return [IsAuthenticated()]

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

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='login')
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Usuario y contraseña requeridos.'}, status=400)

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {'id': user.id, 'username': user.username, 'email': user.email},
            })
        return Response({'error': 'Credenciales inválidas.'}, status=401)
