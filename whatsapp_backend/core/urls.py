from django.urls import path
from . import views

urlpatterns = [
    # Google Calendar
    path('api/google-calendar/auth-url/', views.google_calendar_auth_url, name='google_calendar_auth_url'),
    path('api/google-calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('api/google-calendar/status/', views.google_calendar_status, name='google_calendar_status'),
    path('api/google-calendar/disconnect/', views.google_calendar_disconnect, name='google_calendar_disconnect'),
    path('api/google-calendar/test/', views.test_google_calendar, name='test_google_calendar'),
    
    # AI Settings
    path('api/ai-settings/', views.ai_settings, name='ai_settings'),
    
    # System Stats
    path('api/system/stats/', views.system_stats, name='system_stats'),
] 