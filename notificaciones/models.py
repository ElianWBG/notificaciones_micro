import secrets
from django.db import models


class Cliente(models.Model):
    """Negocio (proyecto) que usa el microservicio.
    Cada cliente tiene su propio API key y configuración de canales."""
    nombre = models.CharField(max_length=200, verbose_name='Nombre del negocio')
    api_key = models.CharField(max_length=64, unique=True, verbose_name='API Key')
    email_from = models.EmailField(blank=True, verbose_name='Email remitente')
    sendgrid_api_key = models.CharField(max_length=300, blank=True, verbose_name='SendGrid API Key')
    # WhatsApp vía Meta Cloud API
    whatsapp_token = models.CharField(max_length=500, blank=True, verbose_name='WhatsApp Token (Meta)')
    whatsapp_phone_id = models.CharField(max_length=50, blank=True, verbose_name='WhatsApp Phone Number ID')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        return self.activo

    @property
    def tiene_whatsapp(self):
        return bool(self.whatsapp_token and self.whatsapp_phone_id)


class Notificacion(models.Model):
    """Registro de cada notificación enviada, pendiente o con error."""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
        ('descartado', 'Descartado'),
    ]
    CANALES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='notificaciones'
    )
    evento = models.CharField(max_length=50, verbose_name='Evento')
    canal = models.CharField(max_length=20, choices=CANALES, verbose_name='Canal')
    destinatario = models.CharField(max_length=300, verbose_name='Destinatario')
    contexto = models.JSONField(default=dict, verbose_name='Contexto')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='pendiente', verbose_name='Estado', db_index=True
    )
    intentos = models.IntegerField(default=0, verbose_name='Intentos')
    enviado_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado en')
    error_mensaje = models.TextField(blank=True, verbose_name='Detalle del error')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', 'intentos']),
        ]

    def __str__(self):
        return f'[{self.evento}] {self.canal} → {self.destinatario} ({self.estado})'
