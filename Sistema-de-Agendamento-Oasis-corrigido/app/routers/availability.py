from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/api/availability",
    tags=["Disponibilidade"],
)


@router.get("", response_model=schemas.AvailabilityResponse)
def check_availability(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    if end_date <= start_date:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="A data final deve ser posterior à data inicial.",
        )

    available, conflicting_bookings, conflicting_blocks = (
        crud.is_period_available(
            db,
            start_date,
            end_date,
        )
    )

    return schemas.AvailabilityResponse(
        start_date=start_date,
        end_date=end_date,
        available=available,
        conflicting_bookings=conflicting_bookings,
        conflicting_blocks=conflicting_blocks,
    )


@router.get("/calendar", response_model=list[schemas.CalendarEntry])
def calendar(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    bookings = crud.list_bookings(
        db,
        start_date=start_date,
        end_date=end_date,
    )

    blocks = crud.list_blocked_dates(
        db,
        start_date=start_date,
        end_date=end_date,
    )

    result = []

    for booking in bookings:
        result.append(
            schemas.CalendarEntry(
                start_date=booking.check_in,
                end_date=booking.check_out,
                type="BOOKING",
                status=booking.status.value,
            )
        )

    for block in blocks:
        result.append(
            schemas.CalendarEntry(
                start_date=block.start_date,
                end_date=block.end_date,
                type="BLOCKED",
                reason=block.reason,
            )
        )

    return result


@router.get("/daily-status", response_model=list[schemas.DailyStatusEntry])
def daily_status(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    if end_date <= start_date:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="A data final deve ser posterior à data inicial.",
        )

    return crud.get_daily_status(
        db,
        start_date,
        end_date,
    )
