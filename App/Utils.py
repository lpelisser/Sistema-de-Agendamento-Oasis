"""
Funções utilitárias / helpers.
"""
from urllib.parse import quote

from app import models

WHATSAPP_NUMBER = "5511966570203"

EVENT_TYPE_LABELS = {
    models.EventType.LAZER_FAMILIA: "Lazer em Família",
    models.EventType.ANIVERSARIO: "Aniversário",
    models.EventType.CASAMENTO: "Casamento",
    models.EventType.CORPORATIVO: "Corporativo",
}


def generate_whatsapp_link(booking: models.Booking) -> str:
    """
    Gera uma URL do WhatsApp com mensagem pré-formatada contendo o resumo
    da solicitação de reserva, para envio ao proprietário da Chácara Oasis.
    """
    evento = EVENT_TYPE_LABELS.get(booking.event_type, booking.event_type)
    check_in = booking.check_in.strftime("%d/%m/%Y")
    check_out = booking.check_out.strftime("%d/%m/%Y")

    valor = (
        f"R$ {booking.total_estimated_value:.2f}"
        if booking.total_estimated_value is not None
        else "A combinar"
    )

    mensagem = (
        "🌳 *Nova Solicitação de Reserva - Chácara Oasis*\n\n"
        f"👤 Cliente: {booking.customer.name}\n"
        f"📞 Contato: {booking.customer.phone}\n"
        f"📅 Check-in: {check_in}\n"
        f"📅 Check-out: {check_out}\n"
        f"👥 Nº de Pessoas: {booking.guests_count}\n"
        f"🎉 Tipo de Evento: {evento}\n"
        f"💰 Valor Estimado: {valor}\n"
        f"📝 Observações: {booking.notes or 'Nenhuma'}\n\n"
        f"ID da Reserva: {booking.id}"
    )

    return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(mensagem)}"