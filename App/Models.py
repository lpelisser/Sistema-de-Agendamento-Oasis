import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship 

from app import Base

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

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(20), nullable=False)  # WhatsApp
    cpf = Column(String(14), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="customer")
    
    
class Booking(Base):
    """Reserva (diária) da Chácara Oasis."""
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)

    guests_count = Column(Integer, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    notes = Column(Text, nullable=True)
    total_estimated_value = Column(Float, nullable=True)

    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDENTE)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indentação corrigida (estava fora da classe)
    customer = relationship("Customer", back_populates="bookings")


class BlockedDate(Base):
    """Bloqueio manual de datas pelo proprietário (manutenção, uso próprio etc.)."""
    __tablename__ = "blocked_dates"

    id = Column(String, primary_key=True, default=generate_uuid)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)