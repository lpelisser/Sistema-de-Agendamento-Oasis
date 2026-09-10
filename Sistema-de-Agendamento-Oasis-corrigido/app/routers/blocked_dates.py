from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/api/blocked-dates",
    tags=["Bloqueios"],
)


@router.post(
    "",
    response_model=schemas.BlockedDateOut,
    status_code=201,
)
def create_blocked_date(
    block_data: schemas.BlockedDateCreate,
    db: Session = Depends(get_db),
):
    available, _, conflicts = crud.is_period_available(
        db,
        block_data.start_date,
        block_data.end_date,
    )

    if conflicts:
        raise HTTPException(
            status_code=409,
            detail="Já existe um bloqueio neste período.",
        )

    if not available:
        raise HTTPException(
            status_code=409,
            detail="Existem reservas neste período.",
        )

    return crud.create_blocked_date(
        db,
        block_data,
    )


@router.get(
    "",
    response_model=list[schemas.BlockedDateOut],
)
def list_blocked_dates(
    db: Session = Depends(get_db),
):
    return crud.list_blocked_dates(db)
