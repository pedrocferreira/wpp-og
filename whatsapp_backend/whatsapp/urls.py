from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WhatsAppMessageViewSet, evolution_webhook, ConnectionStatusView, DisconnectView

router = DefaultRouter()
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/evolution/', evolution_webhook, name='evolution-webhook'),
    path('status/', ConnectionStatusView.as_view(), name='status'),
    path('disconnect/', DisconnectView.as_view(), name='disconnect'),
] 