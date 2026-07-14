"""Canal de Email.

Prioridad de envío:
1. SendGrid (si el Cliente tiene sendgrid_api_key configurado)
2. Django SMTP backend (configuración global del micro)
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from notificaciones.routing import asunto_para

logger = logging.getLogger(__name__)


def enviar_email(notif, cliente):
    """Renderiza la plantilla del evento y envía el correo.

    Lanza una excepción si el envío falla (el caller guarda el error en DB).
    """
    ctx = notif.contexto
    asunto = asunto_para(notif.evento, ctx)

    template_path = f'notificaciones/emails/{notif.evento}.html'
    try:
        html = render_to_string(template_path, ctx)
    except Exception:
        html = render_to_string('notificaciones/emails/generico.html', {
            'asunto': asunto, **ctx
        })

    email_from = cliente.email_from or settings.DEFAULT_FROM_EMAIL

    if cliente.sendgrid_api_key:
        _via_sendgrid(
            api_key=cliente.sendgrid_api_key,
            from_email=email_from,
            to_email=notif.destinatario,
            subject=asunto,
            html=html,
        )
    else:
        _via_smtp(
            from_email=email_from,
            to_email=notif.destinatario,
            subject=asunto,
            html=html,
        )


def _via_sendgrid(api_key, from_email, to_email, subject, html):
    payload = json.dumps({
        'personalizations': [{'to': [{'email': to_email}]}],
        'from': {'email': from_email},
        'subject': subject,
        'content': [{'type': 'text/html', 'value': html}],
    }).encode()
    req = urllib.request.Request(
        'https://api.sendgrid.com/v3/mail/send',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 202):
                raise Exception(f'SendGrid respondió con status {resp.status}')
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        raise Exception(f'SendGrid error {e.code}: {body[:300]}')


def _via_smtp(from_email, to_email, subject, html):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html),
        from_email=from_email,
        to=[to_email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
