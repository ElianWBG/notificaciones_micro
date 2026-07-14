"""Reintenta notificaciones con estado 'error' o 'pendiente' (máx. 3 intentos).

Uso:
    python manage.py reintentar_pendientes
    python manage.py reintentar_pendientes --max-intentos 5
    python manage.py reintentar_pendientes --canal email

En Railway: configura un Cron Job con este comando cada 15 minutos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from notificaciones.canales.email_canal import enviar_email
from notificaciones.canales.whatsapp_canal import enviar_whatsapp
from notificaciones.models import Notificacion


class Command(BaseCommand):
    help = 'Reintenta notificaciones pendientes o con error'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-intentos', type=int, default=3,
            help='Número máximo de intentos antes de descartar (default: 3)',
        )
        parser.add_argument(
            '--canal', type=str, default='',
            help='Filtra por canal: email | whatsapp',
        )

    def handle(self, *args, **options):
        max_intentos = options['max_intentos']
        canal_filtro = options['canal'].strip()

        qs = Notificacion.objects.filter(
            estado__in=('pendiente', 'error'),
            intentos__lt=max_intentos,
        ).select_related('cliente')

        if canal_filtro:
            qs = qs.filter(canal=canal_filtro)

        total = qs.count()
        self.stdout.write(f'Reintentando {total} notificaciones...')

        enviados = 0
        fallidos = 0
        descartados = 0

        for notif in qs:
            notif.intentos += 1
            try:
                if notif.canal == 'email':
                    enviar_email(notif, notif.cliente)
                elif notif.canal == 'whatsapp':
                    enviar_whatsapp(notif, notif.cliente)
                else:
                    notif.estado = 'descartado'
                    notif.error_mensaje = f'Canal "{notif.canal}" no soportado.'
                    notif.save(update_fields=['estado', 'intentos', 'error_mensaje'])
                    descartados += 1
                    continue

                notif.estado = 'enviado'
                notif.enviado_at = timezone.now()
                notif.error_mensaje = ''
                notif.save(update_fields=['estado', 'enviado_at', 'intentos', 'error_mensaje'])
                enviados += 1

            except Exception as exc:
                if notif.intentos >= max_intentos:
                    notif.estado = 'descartado'
                    descartados += 1
                else:
                    notif.estado = 'error'
                    fallidos += 1
                notif.error_mensaje = str(exc)
                notif.save(update_fields=['estado', 'intentos', 'error_mensaje'])
                self.stderr.write(
                    f'  ERROR id={notif.id} [{notif.evento}/{notif.canal}] '
                    f'→ {notif.destinatario}: {exc}'
                )

        self.stdout.write(self.style.SUCCESS(
            f'Resultado: {enviados} enviados, {fallidos} con error, {descartados} descartados.'
        ))
