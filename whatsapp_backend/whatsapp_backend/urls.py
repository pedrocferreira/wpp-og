"""
URL configuration for whatsapp_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import AuthViewSet, ClientViewSet
from .views import home_view
from core import views as core_views

router = routers.DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')
router.register('clients', ClientViewSet, basename='clients')

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/whatsapp/', include('whatsapp.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/google-calendar/auth-url/', core_views.google_calendar_auth_url, name='google_calendar_auth_url'),
    path('api/google-calendar/callback/', core_views.google_calendar_callback, name='google_calendar_callback'),
    path('api/google-calendar/status/', core_views.google_calendar_status, name='google_calendar_status'),
    path('api/google-calendar/disconnect/', core_views.google_calendar_disconnect, name='google_calendar_disconnect'),
    path('api/google-calendar/test/', core_views.google_calendar_test, name='google_calendar_test'),
    path('api/google-calendar/events/', core_views.google_calendar_events, name='google_calendar_events'),
    
    # AI Settings URLs
    path('api/ai-settings/', core_views.ai_settings_get, name='ai_settings_get'),
    path('api/ai-settings/save/', core_views.ai_settings_save, name='ai_settings_save'),
    
    # System Stats
    path('api/system/stats/', core_views.system_stats, name='system_stats'),
]
