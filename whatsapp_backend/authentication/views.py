from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, Client
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer, ClientSerializer

# Create your views here.

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Tenta autenticar usando email
            user = authenticate(
                username=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Se não encontrou por email, tenta por username
            if not user:
                try:
                    user_obj = User.objects.get(email=serializer.validated_data['email'])
                    user = authenticate(
                        username=user_obj.username,
                        password=serializer.validated_data['password']
                    )
                except User.DoesNotExist:
                    user = None
            
            if user:
                refresh = RefreshToken.for_user(user)
                user.is_online = True
                user.save()
                
                return Response({
                    'user': UserSerializer(user).data,
                    'token': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            return Response(
                {'error': 'Credenciais inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'token': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def setup_admin(self, request):
        """Endpoint temporário para criar usuário admin"""
        email = 'admin@admin.com'
        password = 'admin123'
        username = 'admin'
        
        # Remove usuário se existir
        if User.objects.filter(email=email).exists():
            User.objects.filter(email=email).delete()
        
        # Cria novo usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='Sistema',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Gera token automaticamente
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Usuário admin criado com sucesso!',
            'user': UserSerializer(user).data,
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'credentials': {
                'email': email,
                'password': password
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            request.user.is_online = False
            request.user.save()
            RefreshToken(request.data.get('refresh')).blacklist()
            return Response({'message': 'Logout realizado com sucesso'})
        except Exception:
            return Response(
                {'error': 'Erro ao realizar logout'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)
