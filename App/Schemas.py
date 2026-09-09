import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from Models import EventType, BookingStatus

CAPACIDADE_MAXIMA = 20
CAPACIDADE_MINIMA = 1

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=20, description="Telefone/WhatsApp com DDD")
    cpf: str = Field(..., min_length=11, max_length=14)

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos numéricos.")
        return digits
    
class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
        
class BookingCreate(BaseModel):
    customer: CustomerCreate
    check_in: date
    check_out: date
    guests_count: int = Field(..., ge=CAPACIDADE_MINIMA, le=CAPACIDADE_MAXIMA)
    event_type: EventType
    notes: Optional[str] = Field(None, max_length=1000)
    total_estimated_value: Optional[float] = Field(None, ge=0)

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, check_out: date, info):
        check_in = info.data.get("check_in")
        if check_in and check_out <= check_in:
            raise ValueError("A data de check-out deve ser posterior à data de check-in.")
        return check_out


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingOut(BaseModel):
    id: str
    customer: CustomerOut
    check_in: date
    check_out: date
    guests_count: int
    event_type: EventType
    notes: Optional[str]
    total_estimated_value: Optional[float]
    status: BookingStatus
    created_at: datetime

    class Config:
        from_attributes = True
class AvailabilityResponse(BaseModel):
    start_date: date
    end_date: date
    available: bool
    conflicting_bookings: int = 0
    conflicting_blocks: int = 0


class CalendarEntry(BaseModel):
    start_date: date
    end_date: date
    type: str  # "BOOKING" ou "BLOCKED"
    status: Optional[str] = None
    reason: Optional[str] = None
    
class BlockedDateCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = Field(None, max_length=255)

    @field_validator("end_date")
    @classmethod
    def validate_block_dates(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("A data final deve ser igual ou posterior à data inicial.")
        return end_date
    
class DateStatus(str, enum.Enum):
    LIVRE = "LIVRE"
    OCUPADA = "OCUPADA"
    BLOQUEADA = "BLOQUEADA"


class DailyStatusEntry(BaseModel):
    date: date
    status: DateStatus
    booking_id: Optional[str] = None
    reason: Optional[str] = None

class BlockedDateOut(BlockedDateCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True