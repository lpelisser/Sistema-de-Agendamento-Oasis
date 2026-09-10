from datetime import date
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy import Optional

from app import models, schemas 

def get_customer_by_cpf(db: Session, cpf: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.cpf == cpf).first()


def create_customer(db: Session, customer_data: schemas.CustomerCreate) -> models.Customer:
    existing = get_customer_by_cpf(db, customer_data.cpf)
    if existing:
        return existing
    customer = models.Customer(**customer_data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def _has_date_overlap(existing_start: date, existing_end: date,
                       new_start: date, new_end: date) -> bool:
    """Verifica se dois intervalos [start, end) se sobrepõem."""
    return existing_start < new_end and new_start < existing_end


def has_booking_conflict(db: Session, check_in: date, check_out: date,
                          exclude_booking_id: Optional[str] = None) -> int:
    """Conta reservas ativas (não canceladas) que conflitam com o período informado."""
    query = db.query(models.Booking).filter(
        models.Booking.status != models.BookingStatus.CANCELADA,
        models.Booking.check_in < check_out,
        models.Booking.check_out > check_in,
    )
    if exclude_booking_id:
        query = query.filter(models.Booking.id != exclude_booking_id)
    return query.count()


def has_blocked_date_conflict(db: Session, check_in: date, check_out: date) -> int:
    """Conta bloqueios manuais do proprietário que conflitam com o período informado."""
    return db.query(models.BlockedDate).filter(
        models.BlockedDate.start_date < check_out,
        models.BlockedDate.end_date > check_in,
    ).count()


def is_period_available(db: Session, check_in: date, check_out: date,
                         exclude_booking_id: Optional[str] = None) -> tuple[bool, int, int]:
    conflicting_bookings = has_booking_conflict(db, check_in, check_out, exclude_booking_id)
    conflicting_blocks = has_blocked_date_conflict(db, check_in, check_out)
    available = conflicting_bookings == 0 and conflicting_blocks == 0
    return available, conflicting_bookings, conflicting_blocks

def create_booking(db: Session, booking_data: schemas.BookingCreate) -> models.Booking:
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
    return booking


def get_booking(db: Session, booking_id: str) -> Optional[models.Booking]:
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def list_bookings(db: Session, start_date: Optional[date] = None,
                   end_date: Optional[date] = None) -> list[models.Booking]:
    query = db.query(models.Booking).filter(models.Booking.status != models.BookingStatus.CANCELADA)
    if start_date:
        query = query.filter(models.Booking.check_out > start_date)
    if end_date:
        query = query.filter(models.Booking.check_in < end_date)
    return query.order_by(models.Booking.check_in).all()


def update_booking_status(db: Session, booking_id: str,
                           new_status: models.BookingStatus) -> Optional[models.Booking]:
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    return booking

def create_blocked_date(db: Session, block_data: schemas.BlockedDateCreate) -> models.BlockedDate:
    block = models.BlockedDate(**block_data.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block

def get_daily_status(db: Session, start_date: date, end_date: date) -> list[dict]:
    """
    Retorna o status (LIVRE/OCUPADA/BLOQUEADA) de cada dia dentro do intervalo,
    para o ADM visualizar claramente quais datas já estão locadas.
    """
    bookings = list_bookings(db, start_date=start_date, end_date=end_date)
    blocks = list_blocked_dates(db, start_date=start_date, end_date=end_date)

    result = []
    current = start_date
    while current < end_date:
        entry = {"date": current, "status": "LIVRE", "booking_id": None, "reason": None}

        for booking in bookings:
            if booking.check_in <= current < booking.check_out:
                entry["status"] = "OCUPADA"
                entry["booking_id"] = booking.id
                break

        if entry["status"] == "LIVRE":
            for block in blocks:
                if block.start_date <= current <= block.end_date:
                    entry["status"] = "BLOQUEADA"
                    entry["reason"] = block.reason
                    break

        result.append(entry)
        current += timedelta(days=1)

    return result


def list_blocked_dates(db: Session, start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> list[models.BlockedDate]:
    query = db.query(models.BlockedDate)
    if start_date:
        query = query.filter(models.BlockedDate.end_date >= start_date)
    if end_date:
        query = query.filter(models.BlockedDate.start_date <= end_date)
    return query.order_by(models.BlockedDate.start_date).all()
