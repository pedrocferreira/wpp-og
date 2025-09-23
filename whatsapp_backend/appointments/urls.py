from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, analytics_views

router = DefaultRouter()
router.register(r'', views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    # Rotas de Analytics
    path('analytics/dashboard/', analytics_views.dashboard_analytics, name='dashboard-analytics'),
    
    # Rotas específicas
    path('available-slots/', views.get_available_time_slots, name='available-slots'),
    path('book/', views.book_appointment, name='book-appointment'),
    path('success/', views.appointment_success, name='appointment-success'),

    # Rota genérica do roteador por último
    path('', include(router.urls)),
] 