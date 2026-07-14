from rest_framework import serializers
from .models import Notificacion


class EnviarSerializer(serializers.Serializer):
    evento = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True, default='')
    contexto = serializers.DictField(required=False, default=dict)

    def validate(self, data):
        if not data.get('email') and not data.get('telefono'):
            raise serializers.ValidationError(
                'Debe proveer al menos "email" o "telefono".'
            )
        return data


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            'id', 'evento', 'canal', 'destinatario',
            'estado', 'intentos', 'enviado_at', 'error_mensaje', 'created_at',
        ]
        read_only_fields = fields
