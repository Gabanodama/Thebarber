"""
BARBERÍA DISRUPTIVA — Backend FastAPI
Versión Optimizada para Render (Sin dependencias de Redis/Celery)
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Boolean, Text, Enum as SAEnum, Numeric, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum
import os
import logging
import secrets
import string
import pytz
import re
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, EmailStr, field_validator

# ─────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN Y LOGGING
# ─────────────────────────────────────────────────────────────
logger = logging.getLogger("barberia")
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# 2. MODELOS DE BASE DE DATOS
# ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class AppointmentStatus(str, enum.Enum):
    PENDING     = "pending"
    CONFIRMED   = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    CANCELLED   = "cancelled"
    NO_SHOW     = "no_show"

class BarberStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY      = "busy"
    BREAK     = "break"
    OFF       = "off"

class Barber(Base):
    __tablename__ = "barbers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(200))
    bio = Column(Text)
    avatar_url = Column(String(500))
    avatar_initials = Column(String(3))
    color_hex = Column(String(7), default="#C084FC")
    phone = Column(String(20))
    email = Column(String(200), unique=True)
    rating = Column(Numeric(3, 2), default=5.0)
    total_reviews = Column(Integer, default=0)
    status = Column(SAEnum(BarberStatus), default=BarberStatus.AVAILABLE)
    delay_minutes = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    appointments = relationship("Appointment", back_populates="barber")
    schedules = relationship("BarberSchedule", back_populates="barber")
    services = relationship("Service", secondary="barber_services", back_populates="barbers")

class BarberSchedule(Base):
    __tablename__ = "barber_schedules"
    id = Column(Integer, primary_key=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    is_active = Column(Boolean, default=True)
    barber = relationship("Barber", back_populates="schedules")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=60)
    price_cop = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    barbers = relationship("Barber", secondary="barber_services", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")

from sqlalchemy import Table
barber_services = Table(
    "barber_services", Base.metadata,
    Column("barber_id", Integer, ForeignKey("barbers.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id"), primary_key=True),
)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, index=True)
    phone = Column(String(20))
    style_image_url = Column(String(500))
    style_notes = Column(Text)
    preferences = Column(JSON, default={})
    total_visits = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    appointments = relationship("Appointment", back_populates="client")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.CONFIRMED)
    style_image_url = Column(String(500))
    style_notes = Column(Text)
    price_paid = Column(Numeric(10, 2))
    confirmation_code = Column(String(12), unique=True)
    reminder_sent = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancel_reason = Column(String(300))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    barber = relationship("Barber", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

# ─────────────────────────────────────────────────────────────
# 3. SCHEMAS PYDANTIC
# ─────────────────────────────────────────────────────────────
class CreateAppointmentRequest(BaseModel):
    barber_id: int
    service_id: int
    scheduled_at: datetime
    client_name: str
    client_email: EmailStr
    client_phone: Optional[str] = None
    style_notes: Optional[str] = None
    style_image_url: Optional[str] = None

    @field_validator("scheduled_at")
    @classmethod
    def must_be_on_the_hour(cls, v: datetime) -> datetime:
        if v.minute != 0 or v.second != 0:
            raise ValueError("Las citas deben comenzar en punto (minuto 00).")
        return v

class AppointmentResponse(BaseModel):
    id: int
    confirmation_code: str
    barber_name: str
    service_name: str
    scheduled_at: datetime
    ends_at: datetime
    status: str
    price_cop: float
    class Config:
        from_attributes = True

class BarberStatusUpdate(BaseModel):
    status: BarberStatus
    delay_minutes: int = 0

# ─────────────────────────────────────────────────────────────
# 4. FUNCIONES DE APOYO Y NOTIFICACIONES (SÍNCRONAS)
# ─────────────────────────────────────────────────────────────
SLOT_DURATION = timedelta(minutes=60)

def generate_confirmation_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "BD-" + "".join(secrets.choice(chars) for _ in range(6))

def send_confirmation_notification(appointment_id: int):
    """Ejecución directa sin Celery"""
    logger.info(f"[NOTIF] Confirmación simulada enviada → cita #{appointment_id}")

def schedule_reminder(appointment_id: int, scheduled_at: datetime):
    """Simulación de recordatorio"""
    logger.info(f"[SCHEDULER] Recordatorio programado localmente para cita #{appointment_id}")

async def check_availability(db: AsyncSession, barber_id: int, scheduled_at: datetime) -> bool:
    slot_end = scheduled_at + SLOT_DURATION
    conflict = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.barber_id == barber_id,
                Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
                Appointment.scheduled_at < slot_end,
                Appointment.ends_at > scheduled_at,
            )
        )
    )
    return conflict.scalar_one_or_none() is None

# ─────────────────────────────────────────────────────────────
# 5. CONFIGURACIÓN FASTAPI Y DB
# ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost/barberia_db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

app = FastAPI(title="Barbería Disruptiva API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with SessionLocal() as session:
        yield session

# ─────────────────────────────────────────────────────────────
# 6. ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/barbers")
async def list_barbers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Barber).where(Barber.is_active == True))
    return result.scalars().all()

@app.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def create_appointment(payload: CreateAppointmentRequest, db: AsyncSession = Depends(get_db)):
    # 1. Validaciones
    barber = (await db.execute(select(Barber).where(Barber.id == payload.barber_id))).scalar_one_or_none()
    if not barber: raise HTTPException(404, "Barbero no encontrado")
    
    service = (await db.execute(select(Service).where(Service.id == payload.service_id))).scalar_one_or_none()
    if not service: raise HTTPException(404, "Servicio no encontrado")

    if not await check_availability(db, payload.barber_id, payload.scheduled_at):
        raise HTTPException(409, "Horario ocupado")

    # 2. Cliente
    res_client = await db.execute(select(Client).where(Client.email == payload.client_email))
    client = res_client.scalar_one_or_none()
    if not client:
        client = Client(name=payload.client_name, email=payload.client_email, phone=payload.client_phone)
        db.add(client)
        await db.flush()

    # 3. Crear Cita
    new_appt = Appointment(
        barber_id=payload.barber_id,
        client_id=client.id,
        service_id=payload.service_id,
        scheduled_at=payload.scheduled_at,
        ends_at=payload.scheduled_at + SLOT_DURATION,
        confirmation_code=generate_confirmation_code(),
        price_paid=service.price_cop,
        confirmed_at=datetime.utcnow()
    )
    db.add(new_appt)
    client.total_visits += 1
    await db.commit()
    await db.refresh(new_appt)

    # 4. Notificaciones (Llamada directa, sin .delay)
    send_confirmation_notification(new_appt.id)
    schedule_reminder(new_appt.id, payload.scheduled_at)

    return AppointmentResponse(
        id=new_appt.id,
        confirmation_code=new_appt.confirmation_code,
        barber_name=barber.name,
        service_name=service.name,
        scheduled_at=new_appt.scheduled_at,
        ends_at=new_appt.ends_at,
        status=new_appt.status,
        price_cop=float(service.price_cop)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)