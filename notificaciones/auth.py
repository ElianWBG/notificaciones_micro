import secrets
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Cliente


class ApiKeyAuthentication(BaseAuthentication):
    """Autentica vía 'Authorization: Bearer <api_key>'.
    request.user será la instancia de Cliente autenticado."""

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        token = auth[7:].strip()
        try:
            cliente = Cliente.objects.get(activo=True, api_key=token)
        except Cliente.DoesNotExist:
            raise AuthenticationFailed('API Key inválida o inactiva.')
        return (cliente, None)

    def authenticate_header(self, request):
        return 'Bearer realm="notificaciones-api"'
