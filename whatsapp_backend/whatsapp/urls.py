from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'messages', views.WhatsAppMessageViewSet)

urlpatterns = [
    # ViewSets via router
    path('', include(router.urls)),
    
    # Webhook Evolution API (captura qualquer endpoint específico)
    path('webhook/evolution/', views.WebhookView.as_view(), name='evolution_webhook'),
    path('webhook/evolution/<str:event_type>/', views.WebhookView.as_view(), name='evolution_webhook_specific'),
    # Rotas sem barra final para compatibilidade com Evolution API
    path('webhook/evolution/<str:event_type>', views.WebhookView.as_view(), name='evolution_webhook_no_slash'),
    
    # === ENDPOINTS DE MONITORAMENTO (NOVOS) ===
    # Status de saúde do sistema
    path('monitoring/health/', views.MonitoringView.as_view(), name='monitoring_health'),
    
    # Alertas do sistema
    path('monitoring/alerts/', views.AlertsView.as_view(), name='monitoring_alerts'),
    
    # Métricas de performance
    path('monitoring/metrics/', views.MetricsView.as_view(), name='monitoring_metrics'),
    
    # Estatísticas das filas
    path('monitoring/queue-stats/', views.QueueStatsView.as_view(), name='queue_stats'),
    
    # Reprocessar mensagens falhadas
    path('monitoring/retry-failed/', views.RetryFailedMessagesView.as_view(), name='retry_failed_messages'),
    
    # Status de tarefa específica
    path('monitoring/task/<str:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
] 