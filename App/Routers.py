from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.utils import generate_whatsapp_link
from app.services.email_service import send_email_notification

router = APIRouter(prefix="/api/bookings", tags=["Reservas"])


@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(
    booking_data: schemas.BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Cria uma nova solicitação de reserva.
    Valida sobreposição de datas contra reservas ativas e bloqueios manuais
    antes de persistir no banco de dados. Assim que o registro sobe para o
    banco, dispara em background o envio automático da notificação ao ADM
    por e-mail (SMTP).
    """
    available, conflicting_bookings, conflicting_blocks = crud.is_period_available(
        db, booking_data.check_in, booking_data.check_out
    )

    if not available:
        detail = "Período indisponível."
        if conflicting_bookings:
            detail += f" {conflicting_bookings} reserva(s) já ocupam este período."
        if conflicting_blocks:
            detail += f" {conflicting_blocks} data(s) bloqueada(s) pelo proprietário."
        raise HTTPException(status_code=409, detail=detail)

    booking = crud.create_booking(db, booking_data)

    # Envio assíncrono (não bloqueia a resposta da API ao cliente)
    background_tasks.add_task(send_email_notification, booking)

    return booking


@router.get("/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de uma reserva específica."""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return booking


@router.patch("/{booking_id}/status", response_model=schemas.BookingOut)
def update_status(
    booking_id: str,
    status_data: schemas.BookingStatusUpdate,
    db: Session = Depends(get_db),
):
    """Altera o status de uma reserva (ex.: confirmar após pagamento do sinal)."""
    booking = crud.update_booking_status(db, booking_id, status_data.status)
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return booking


@router.get("/{booking_id}/whatsapp-link")
def get_whatsapp_link(booking_id: str, db: Session = Depends(get_db)):
    """Retorna o link do WhatsApp com o resumo da reserva para envio manual ao proprietário."""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return {"whatsapp_link": generate_whatsapp_link(booking)}
