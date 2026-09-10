from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models
from app.routers import availability, blocked_dates, bookings

# Cria as tabelas automaticamente.
# Para produção, recomenda-se usar Alembic/migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chácara Oasis - API de Reservas",
    description="Backend do sistema de gestão e agendamento da Chácara Oasis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookings.router)
app.include_router(availability.router)
app.include_router(blocked_dates.router)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "service": "Chácara Oasis API",
    }


@app.get("/health", tags=["Health Check"])
def health():
    return {"status": "ok"}
