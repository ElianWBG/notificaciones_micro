"""Canal de WhatsApp vía Meta Cloud API.

Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages
Funciona en la ventana de 24 h de una conversación activa, o con plantillas aprobadas.
"""
import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

MENSAJES = {
    'pedido_nuevo': (
        '🛒 *Nuevo pedido #{pedido_id}*\n'
        'Cliente: {nombre_cliente}\n'
        'Total: ${total}\n'
        '{panel_url}'
    ),
    'pedido_confirmado': (
        '✅ Hola {nombre_cliente}, tu pedido #{pedido_id} en *{store_name}* fue confirmado.\n'
        'Total: ${total}\n¡Gracias por tu compra!'
    ),
    'cuota_vencida': (
        '⚠️ {nombre_cliente}, tienes una cuota vencida de *${valor}* '
        '(Cuota {cuota_numero} / Factura #{factura_id}) en *{store_name}*.\n'
        'Contáctanos para regularizarla.'
    ),
    'stock_bajo': (
        '⚠️ *Stock bajo*\nProducto: {nombre_producto}\n'
        'Stock actual: {stock} unidades\n{panel_url}'
    ),
    'bienvenida': (
        '¡Hola {nombre_cliente}! Bienvenido/a a *{store_name}*. '
        'Ya puedes iniciar sesión y explorar nuestro catálogo.'
    ),
}


def enviar_whatsapp(notif, cliente):
    """Envía un mensaje de texto vía WhatsApp Cloud API.

    Lanza excepción si el cliente no tiene WhatsApp configurado o si falla el envío.
    """
    if not cliente.tiene_whatsapp:
        raise ValueError('WhatsApp no configurado para este cliente (falta token o phone_id).')

    ctx = notif.contexto
    texto_template = MENSAJES.get(
        notif.evento,
        'Notificación de {store_name}: {mensaje}'
    )
    try:
        texto = texto_template.format_map({
            **ctx,
            'mensaje': ctx.get('mensaje', ''),
            'panel_url': ctx.get('panel_url', ''),
        })
    except KeyError as e:
        raise ValueError(f'Falta la variable {e} en el contexto para el evento "{notif.evento}"')

    phone = _normalizar_telefono(notif.destinatario)

    payload = json.dumps({
        'messaging_product': 'whatsapp',
        'to': phone,
        'type': 'text',
        'text': {'preview_url': False, 'body': texto},
    }).encode()

    url = f'https://graph.facebook.com/v19.0/{cliente.whatsapp_phone_id}/messages'
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {cliente.whatsapp_token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            logger.info('WhatsApp enviado a %s (msg_id=%s)', phone, result.get('messages', [{}])[0].get('id'))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        raise Exception(f'WhatsApp API error {e.code}: {body[:300]}')


def _normalizar_telefono(raw: str) -> str:
    """Normaliza al formato E.164 sin '+' (requerido por Meta API)."""
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        digits = '593' + digits[1:]
    elif len(digits) == 9:
        digits = '593' + digits
    return digits
