import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class EventType(str, enum.Enum):
    LAZER_FAMILIA = "LAZER_FAMILIA"
    ANIVERSARIO = "ANIVERSARIO"
    CASAMENTO = "CASAMENTO"
    CORPORATIVO = "CORPORATIVO"


class BookingStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"
    CONCLUIDO = "CONCLUIDO"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    cpf = Column(String(11), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    bookings = relationship(
        "Booking",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    guests_count = Column(Integer, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    notes = Column(Text, nullable=True)
    total_estimated_value = Column(Float, nullable=True)
    status = Column(
        Enum(BookingStatus),
        nullable=False,
        default=BookingStatus.PENDENTE,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="bookings")


class BlockedDate(Base):
    __tablename__ = "blocked_dates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
