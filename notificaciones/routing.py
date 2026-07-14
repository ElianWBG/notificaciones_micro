"""Mapea cada evento a los canales que deben recibirlo.

Los canales se intentan en orden. Si el contexto no tiene los datos
necesarios para un canal (p. ej. telefono vacío), ese canal se omite.
"""

ROUTING: dict[str, list[str]] = {
    'bienvenida':        ['email'],
    'pedido_nuevo':      ['email', 'whatsapp'],
    'pedido_confirmado': ['email'],
    'cuota_vencida':     ['email'],
    'stock_bajo':        ['email', 'whatsapp'],
    'promocion':         ['email'],
}

ASUNTOS = {
    'bienvenida':        '¡Bienvenido/a a {store_name}!',
    'pedido_nuevo':      '[Nueva venta] Pedido #{pedido_id} de {nombre_cliente}',
    'pedido_confirmado': 'Tu pedido #{pedido_id} fue confirmado ✓',
    'cuota_vencida':     'Recordatorio: cuota vencida – {store_name}',
    'stock_bajo':        '[ALERTA] Stock bajo: {nombre_producto}',
    'promocion':         '{asunto}',
}


def canales_para(evento: str) -> list[str]:
    return ROUTING.get(evento, ['email'])


def asunto_para(evento: str, contexto: dict) -> str:
    template = ASUNTOS.get(evento, 'Notificación de {store_name}')
    try:
        return template.format_map({**contexto, 'asunto': contexto.get('asunto', 'Notificación')})
    except KeyError:
        return template.replace('{', '').replace('}', '')
