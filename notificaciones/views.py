import logging

from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import ApiKeyAuthentication
from .canales.email_canal import enviar_email
from .canales.whatsapp_canal import enviar_whatsapp
from .models import Notificacion
from .routing import canales_para
from .serializers import EnviarSerializer, NotificacionSerializer

logger = logging.getLogger(__name__)


class EnviarNotificacionView(APIView):
    """POST /api/v1/enviar/

    Recibe un evento + destinatario + contexto, envía por todos los canales
    configurados para ese evento y devuelve el resultado.

    Body:
        evento      str   Nombre del evento (ej: "pedido_confirmado")
        email       str   Email del destinatario (opcional)
        telefono    str   Teléfono del destinatario con código país (opcional)
        contexto    dict  Variables para la plantilla

    Response 202:
        enviados    list  Canales por los que se envió exitosamente
        fallidos    list  Canales que fallaron con su error
        ids         list  IDs de los registros Notificacion creados
    """
    authentication_classes = [ApiKeyAuthentication]

    def post(self, request):
        cliente = request.user
        serializer = EnviarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        d = serializer.validated_data
        evento = d['evento']
        email = d.get('email', '')
        telefono = d.get('telefono', '')
        contexto = d.get('contexto', {})

        canales = canales_para(evento)
        enviados = []
        fallidos = []
        ids = []

        for canal in canales:
            destinatario = email if canal == 'email' else telefono
            if not destinatario:
                continue

            notif = Notificacion.objects.create(
                cliente=cliente,
                evento=evento,
                canal=canal,
                destinatario=destinatario,
                contexto=contexto,
            )
            ids.append(notif.id)

            try:
                if canal == 'email':
                    enviar_email(notif, cliente)
                elif canal == 'whatsapp':
                    enviar_whatsapp(notif, cliente)

                notif.estado = 'enviado'
                notif.enviado_at = timezone.now()
                notif.intentos = 1
                notif.save(update_fields=['estado', 'enviado_at', 'intentos'])
                enviados.append(canal)

            except Exception as exc:
                notif.estado = 'error'
                notif.intentos = 1
                notif.error_mensaje = str(exc)
                notif.save(update_fields=['estado', 'intentos', 'error_mensaje'])
                fallidos.append({'canal': canal, 'error': str(exc)})
                logger.error(
                    'Error enviando [%s/%s] a %s para cliente %s: %s',
                    evento, canal, destinatario, cliente.nombre, exc,
                )

        status_code = 202 if enviados else (400 if not ids else 200)
        return Response({'enviados': enviados, 'fallidos': fallidos, 'ids': ids}, status=status_code)


class NotificacionListView(APIView):
    """GET /api/v1/notificaciones/?estado=error&limite=50

    Devuelve el historial de notificaciones del cliente autenticado.
    Útil para monitoreo y auditoría.
    """
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        cliente = request.user
        qs = Notificacion.objects.filter(cliente=cliente)

        estado = request.query_params.get('estado', '').strip()
        if estado:
            qs = qs.filter(estado=estado)

        evento = request.query_params.get('evento', '').strip()
        if evento:
            qs = qs.filter(evento=evento)

        try:
            limite = min(int(request.query_params.get('limite', 100)), 500)
        except ValueError:
            limite = 100

        serializer = NotificacionSerializer(qs[:limite], many=True)
        return Response({'total': qs.count(), 'resultados': serializer.data})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def health_check(request):
    """GET /api/v1/health/ — sin autenticación, para Railway / uptime checks."""
    return Response({'status': 'ok'})
