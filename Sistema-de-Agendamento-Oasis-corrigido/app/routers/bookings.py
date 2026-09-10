from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.services.email_service import send_email_notification
from app.utils import generate_whatsapp_link

router = APIRouter(
    prefix="/api/bookings",
    tags=["Reservas"],
)


def _email_data(booking) -> dict:
    return {
        "booking_id": booking.id,
        "customer_name": booking.customer.name,
        "customer_email": booking.customer.email,
        "customer_phone": booking.customer.phone,
        "customer_cpf": booking.customer.cpf,
        "check_in": booking.check_in.strftime("%d/%m/%Y"),
        "check_out": booking.check_out.strftime("%d/%m/%Y"),
        "guests_count": booking.guests_count,
        "event_type": booking.event_type.value,
        "notes": booking.notes,
        "total_estimated_value": booking.total_estimated_value,
        "status": booking.status.value,
    }


@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(
    booking_data: schemas.BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    available, conflicting_bookings, conflicting_blocks = (
        crud.is_period_available(
            db,
            booking_data.check_in,
            booking_data.check_out,
        )
    )

    if not available:
        detail = "Período indisponível."

        if conflicting_bookings:
            detail += (
                f" {conflicting_bookings} reserva(s) já ocupam este período."
            )

        if conflicting_blocks:
            detail += (
                f" {conflicting_blocks} bloqueio(s) impedem a reserva."
            )

        raise HTTPException(
            status_code=409,
            detail=detail,
        )

    booking = crud.create_booking(db, booking_data)

    # O registro já foi confirmado no banco neste ponto.
    # O e-mail recebe somente dados simples, evitando depender
    # da sessão SQLAlchemy depois que a requisição terminar.
    background_tasks.add_task(
        send_email_notification,
        _email_data(booking),
    )

    return booking


@router.get("/{booking_id}", response_model=schemas.BookingOut)
def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
):
    booking = crud.get_booking(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Reserva não encontrada.",
        )

    return booking


@router.patch(
    "/{booking_id}/status",
    response_model=schemas.BookingOut,
)
def update_status(
    booking_id: str,
    status_data: schemas.BookingStatusUpdate,
    db: Session = Depends(get_db),
):
    booking = crud.update_booking_status(
        db,
        booking_id,
        status_data.status,
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Reserva não encontrada.",
        )

    return booking


@router.get("/{booking_id}/whatsapp-link")
def whatsapp_link(
    booking_id: str,
    db: Session = Depends(get_db),
):
    booking = crud.get_booking(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Reserva não encontrada.",
        )

    return {
        "booking_id": booking.id,
        "whatsapp_url": generate_whatsapp_link(booking),
    }
