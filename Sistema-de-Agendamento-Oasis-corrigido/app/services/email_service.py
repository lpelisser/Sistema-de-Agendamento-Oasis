import logging
import os
import smtplib
from email.message import EmailMessage
from html import escape

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

EVENT_TYPE_LABELS = {
    "LAZER_FAMILIA": "Lazer em Família",
    "ANIVERSARIO": "Aniversário",
    "CASAMENTO": "Casamento",
    "CORPORATIVO": "Corporativo",
}


def _format_money(value):
    if value is None:
        return "A combinar"

    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_booking_email(data: dict) -> EmailMessage:
    event_type = EVENT_TYPE_LABELS.get(
        data["event_type"],
        data["event_type"],
    )

    check_in = data["check_in"]
    check_out = data["check_out"]

    subject = (
        f"Nova solicitação de reserva - Chácara Oasis "
        f"({data['customer_name']})"
    )

    text_body = f"""Nova Solicitação de Reserva - Chácara Oasis

Cliente: {data['customer_name']}
E-mail: {data['customer_email']}
Telefone: {data['customer_phone']}
CPF: {data['customer_cpf']}

Check-in: {check_in}
Check-out: {check_out}
Número de pessoas: {data['guests_count']}
Tipo de evento: {event_type}
Valor estimado: {_format_money(data['total_estimated_value'])}

Observações:
{data['notes'] or 'Nenhuma'}

ID da reserva: {data['booking_id']}
Status: {data['status']}
"""

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <h2>🌳 Nova solicitação de reserva - Chácara Oasis</h2>

        <h3>Cliente</h3>
        <p>
          <strong>Nome:</strong> {escape(data['customer_name'])}<br>
          <strong>E-mail:</strong> {escape(data['customer_email'])}<br>
          <strong>Telefone:</strong> {escape(data['customer_phone'])}<br>
          <strong>CPF:</strong> {escape(data['customer_cpf'])}
        </p>

        <h3>Reserva</h3>
        <p>
          <strong>Check-in:</strong> {check_in}<br>
          <strong>Check-out:</strong> {check_out}<br>
          <strong>Pessoas:</strong> {data['guests_count']}<br>
          <strong>Evento:</strong> {escape(event_type)}<br>
          <strong>Valor estimado:</strong> {_format_money(data['total_estimated_value'])}<br>
          <strong>Status:</strong> {escape(data['status'])}
        </p>

        <h3>Observações</h3>
        <p>{escape(data['notes'] or 'Nenhuma')}</p>

        <hr>

        <p>
          <strong>ID da reserva:</strong> {escape(data['booking_id'])}
        </p>
      </body>
    </html>
    """

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_USER or ""
    message["To"] = ADMIN_EMAIL or ""
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    return message


def send_email_notification(data: dict) -> bool:
    """Envia o resumo da reserva para o e-mail do ADM."""
    if not SMTP_USER or not SMTP_PASSWORD or not ADMIN_EMAIL:
        logger.error(
            "SMTP_USER, SMTP_PASSWORD e ADMIN_EMAIL devem estar configurados."
        )
        return False

    message = build_booking_email(data)

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20,
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

        logger.info(
            "E-mail da reserva %s enviado para %s.",
            data["booking_id"],
            ADMIN_EMAIL,
        )
        return True

    except (smtplib.SMTPException, OSError) as exc:
        logger.exception(
            "Falha ao enviar e-mail da reserva %s: %s",
            data["booking_id"],
            exc,
        )
        return False
