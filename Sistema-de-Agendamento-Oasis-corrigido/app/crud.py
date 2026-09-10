from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app import models, schemas


def get_customer_by_cpf(db: Session, cpf: str) -> Optional[models.Customer]:
    return (
        db.query(models.Customer)
        .filter(models.Customer.cpf == cpf)
        .first()
    )


def create_customer(
    db: Session,
    customer_data: schemas.CustomerCreate,
) -> models.Customer:
    existing = get_customer_by_cpf(db, customer_data.cpf)

    if existing:
        existing.name = customer_data.name
        existing.email = str(customer_data.email)
        existing.phone = customer_data.phone
        db.flush()
        return existing

    customer = models.Customer(
        **customer_data.model_dump(),
        email=str(customer_data.email),
    )
    db.add(customer)
    db.flush()
    return customer


def has_booking_conflict(
    db: Session,
    check_in: date,
    check_out: date,
    exclude_booking_id: Optional[str] = None,
) -> int:
    query = (
        db.query(models.Booking)
        .filter(
            models.Booking.status != models.BookingStatus.CANCELADO,
            models.Booking.check_in < check_out,
            models.Booking.check_out > check_in,
        )
    )

    if exclude_booking_id:
        query = query.filter(models.Booking.id != exclude_booking_id)

    return query.count()


def has_blocked_date_conflict(
    db: Session,
    check_in: date,
    check_out: date,
) -> int:
    return (
        db.query(models.BlockedDate)
        .filter(
            models.BlockedDate.start_date < check_out,
            models.BlockedDate.end_date > check_in,
        )
        .count()
    )


def is_period_available(
    db: Session,
    check_in: date,
    check_out: date,
    exclude_booking_id: Optional[str] = None,
):
    conflicting_bookings = has_booking_conflict(
        db,
        check_in,
        check_out,
        exclude_booking_id,
    )
    conflicting_blocks = has_blocked_date_conflict(
        db,
        check_in,
        check_out,
    )

    return (
        conflicting_bookings == 0 and conflicting_blocks == 0,
        conflicting_bookings,
        conflicting_blocks,
    )


def create_booking(
    db: Session,
    booking_data: schemas.BookingCreate,
) -> models.Booking:
    customer = create_customer(db, booking_data.customer)

    booking = models.Booking(
        customer_id=customer.id,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        guests_count=booking_data.guests_count,
        event_type=booking_data.event_type,
        notes=booking_data.notes,
        total_estimated_value=booking_data.total_estimated_value,
        status=models.BookingStatus.PENDENTE,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Garante que customer esteja carregado antes da sessão ser fechada.
    booking = (
        db.query(models.Booking)
        .options(joinedload(models.Booking.customer))
        .filter(models.Booking.id == booking.id)
        .first()
    )

    return booking


def get_booking(
    db: Session,
    booking_id: str,
) -> Optional[models.Booking]:
    return (
        db.query(models.Booking)
        .options(joinedload(models.Booking.customer))
        .filter(models.Booking.id == booking_id)
        .first()
    )


def list_bookings(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    query = (
        db.query(models.Booking)
        .options(joinedload(models.Booking.customer))
        .filter(models.Booking.status != models.BookingStatus.CANCELADO)
    )

    if start_date:
        query = query.filter(models.Booking.check_out > start_date)

    if end_date:
        query = query.filter(models.Booking.check_in < end_date)

    return query.order_by(models.Booking.check_in).all()


def update_booking_status(
    db: Session,
    booking_id: str,
    new_status: models.BookingStatus,
):
    booking = get_booking(db, booking_id)

    if not booking:
        return None

    booking.status = new_status
    db.commit()
    db.refresh(booking)

    return get_booking(db, booking_id)


def create_blocked_date(
    db: Session,
    block_data: schemas.BlockedDateCreate,
):
    block = models.BlockedDate(**block_data.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def list_blocked_dates(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    query = db.query(models.BlockedDate)

    if start_date:
        query = query.filter(models.BlockedDate.end_date >= start_date)

    if end_date:
        query = query.filter(models.BlockedDate.start_date <= end_date)

    return query.order_by(models.BlockedDate.start_date).all()


def get_daily_status(
    db: Session,
    start_date: date,
    end_date: date,
):
    bookings = list_bookings(
        db,
        start_date=start_date,
        end_date=end_date,
    )
    blocks = list_blocked_dates(
        db,
        start_date=start_date,
        end_date=end_date,
    )

    result = []
    current = start_date

    while current < end_date:
        entry = {
            "date": current,
            "status": "LIVRE",
            "booking_id": None,
            "reason": None,
        }

        for booking in bookings:
            if booking.check_in <= current < booking.check_out:
                entry["status"] = "OCUPADA"
                entry["booking_id"] = booking.id
                break

        if entry["status"] == "LIVRE":
            for block in blocks:
                if block.start_date <= current < block.end_date:
                    entry["status"] = "BLOQUEADA"
                    entry["reason"] = block.reason
                    break

        result.append(entry)
        current += timedelta(days=1)

    return result
