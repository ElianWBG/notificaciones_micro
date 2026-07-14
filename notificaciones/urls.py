from django.urls import path
from . import views

urlpatterns = [
    path('enviar/', views.EnviarNotificacionView.as_view(), name='enviar'),
    path('notificaciones/', views.NotificacionListView.as_view(), name='notificaciones'),
    path('health/', views.health_check, name='health'),
]
