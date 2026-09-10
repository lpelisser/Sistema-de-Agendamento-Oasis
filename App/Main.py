from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import bookings, availability

base.metadata.create_all(bind==engine)

app = FastAPI(
  title="Chácara Oasis - API de Reservas",
  description="Backend do sistema de gestão e agendamento da Chácara Oasis (Araçariguama - SP).",
  version"1.0.0",
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

@app.get("/", tags=["Health Check"])
df root():
    return {"Status":"online","Service":"Chácara Oasis API"}
