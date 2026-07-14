from django.contrib import admin
from .models import Cliente, Notificacion


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email_from', 'tiene_whatsapp', 'activo', 'created_at']
    list_filter = ['activo']
    search_fields = ['nombre', 'email_from']
    readonly_fields = ['api_key', 'created_at']

    def tiene_whatsapp(self, obj):
        return obj.tiene_whatsapp
    tiene_whatsapp.boolean = True
    tiene_whatsapp.short_description = 'WhatsApp'


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['evento', 'canal', 'destinatario', 'estado', 'intentos', 'enviado_at', 'created_at']
    list_filter = ['estado', 'canal', 'evento', 'cliente']
    search_fields = ['destinatario', 'evento']
    readonly_fields = ['created_at', 'enviado_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
