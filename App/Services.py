import logging
import os
import smtplib
from email.mime.text import MIMEText

from app import models

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

EVENT_TYPE_LABELS = {
    models.EventType.LAZER_FAMILIA: "Lazer em Família",
    models.EventType.ANIVERSARIO: "Aniversário",
    models.EventType.CASAMENTO: "Casamento",
    models.EventType.CORPORATIVO: "Corporativo",
}


def _build_message_body(booking: models.Booking) -> str:
    evento = EVENT_TYPE_LABELS.get(booking.event_type, booking.event_type)
    check_in = booking.check_in.strftime("%d/%m/%Y")
    check_out = booking.check_out.strftime("%d/%m/%Y")
    valor = (
        f"R$ {booking.total_estimated_value:.2f}"
        if booking.total_estimated_value is not None
        else "A combinar"
    )

    return (
        "Nova Solicitação de Reserva - Chácara Oasis\n\n"
        f"Cliente: {booking.customer.name}\n"
        f"Contato: {booking.customer.phone}\n"
        f"CPF: {booking.customer.cpf}\n"
        f"Check-in: {check_in}\n"
        f"Check-out: {check_out}\n"
        f"Nº de Pessoas: {booking.guests_count}\n"
        f"Tipo de Evento: {evento}\n"
        f"Valor Estimado: {valor}\n"
        f"Observações: {booking.notes or 'Nenhuma'}\n\n"
        f"ID da Reserva: {booking.id}"
    )


def send_email_notification(booking: models.Booking) -> bool:
    """Envia notificação automática ao ADM por e-mail assim que a reserva é criada."""
    if not SMTP_USER or not SMTP_PASSWORD or not ADMIN_EMAIL:
        logger.warning(
            "SMTP_USER, SMTP_PASSWORD ou ADMIN_EMAIL não configurados. "
            "Notificação não enviada."
        )
        return False

    message = MIMEText(_build_message_body(booking), _charset="utf-8")
    message["Subject"] = f"Nova Reserva - Chácara Oasis ({booking.customer.name})"
    message["From"] = SMTP_USER
    message["To"] = ADMIN_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [ADMIN_EMAIL], message.as_string())
        logger.info("Notificação e-mail enviada para reserva %s", booking.id)
        return True
    except smtplib.SMTPException as exc:
        logger.error(
            "Falha ao enviar notificação e-mail para reserva %s: %s",
            booking.id, exc,
        )
        return False
