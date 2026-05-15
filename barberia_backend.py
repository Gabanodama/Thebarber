"""
BARBERÍA DISRUPTIVA — Backend FastAPI
Stack: Python 3.11 · FastAPI · SQLAlchemy (async) · PostgreSQL · Redis · Celery
"""

# ─────────────────────────────────────────────────────────────
# 1. MODELOS DE BASE DE DATOS (SQLAlchemy)
# ─────────────────────────────────────────────────────────────

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Boolean, Text, Enum as SAEnum, Numeric, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum

class Base(DeclarativeBase):
    pass

class AppointmentStatus(str, enum.Enum):
    PENDING    = "pending"
    CONFIRMED  = "confirmed"
    IN_PROGRESS= "in_progress"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"
    NO_SHOW    = "no_show"

class BarberStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY      = "busy"
    BREAK     = "break"
    OFF       = "off"

# ── Tabla: barbers ──────────────────────────────────────────
class Barber(Base):
    __tablename__ = "barbers"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    specialty     = Column(String(200))
    bio           = Column(Text)
    avatar_url    = Column(String(500))
    avatar_initials = Column(String(3))
    color_hex     = Column(String(7), default="#C084FC")
    phone         = Column(String(20))
    email         = Column(String(200), unique=True)
    rating        = Column(Numeric(3, 2), default=5.0)
    total_reviews = Column(Integer, default=0)
    status        = Column(SAEnum(BarberStatus), default=BarberStatus.AVAILABLE)
    delay_minutes = Column(Integer, default=0)   # negativo = adelantado
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    appointments  = relationship("Appointment", back_populates="barber")
    schedules     = relationship("BarberSchedule", back_populates="barber")
    services      = relationship("Service", secondary="barber_services", back_populates="barbers")

# ── Tabla: barber_schedules (disponibilidad semanal) ────────
class BarberSchedule(Base):
    __tablename__ = "barber_schedules"

    id          = Column(Integer, primary_key=True)
    barber_id   = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Lun, 6=Dom
    start_time  = Column(String(5), nullable=False)  # "08:00"
    end_time    = Column(String(5), nullable=False)   # "20:00"
    is_active   = Column(Boolean, default=True)

    barber      = relationship("Barber", back_populates="schedules")

# ── Tabla: services ─────────────────────────────────────────
class Service(Base):
    __tablename__ = "services"

    id              = Column(Integer, primary_key=True)
    name            = Column(String(100), nullable=False)
    description     = Column(Text)
    duration_minutes= Column(Integer, default=60)   # SIEMPRE 60
    price_cop       = Column(Numeric(10, 2), nullable=False)
    is_active       = Column(Boolean, default=True)

    barbers         = relationship("Barber", secondary="barber_services", back_populates="services")
    appointments    = relationship("Appointment", back_populates="service")

# ── Tabla pivote: barber_services ───────────────────────────
from sqlalchemy import Table
barber_services = Table(
    "barber_services", Base.metadata,
    Column("barber_id", Integer, ForeignKey("barbers.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id"), primary_key=True),
)

# ── Tabla: clients ──────────────────────────────────────────
class Client(Base):
    __tablename__ = "clients"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(150), nullable=False)
    email           = Column(String(200), unique=True, index=True)
    phone           = Column(String(20))
    style_image_url = Column(String(500))     # foto de referencia de estilo
    style_notes     = Column(Text)            # notas del perfil de estilo
    preferences     = Column(JSON, default={})
    total_visits    = Column(Integer, default=0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    appointments    = relationship("Appointment", back_populates="client")

# ── Tabla: appointments ─────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"

    id              = Column(Integer, primary_key=True, index=True)
    barber_id       = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id      = Column(Integer, ForeignKey("services.id"), nullable=False)

    scheduled_at    = Column(DateTime(timezone=True), nullable=False)  # inicio exacto
    ends_at         = Column(DateTime(timezone=True), nullable=False)   # siempre +60 min

    status          = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.CONFIRMED)
    style_image_url = Column(String(500))   # foto subida para ESTA cita
    style_notes     = Column(Text)          # nota para el barbero
    price_paid      = Column(Numeric(10, 2))
    confirmation_code = Column(String(12), unique=True)

    reminder_sent   = Column(Boolean, default=False)
    confirmed_at    = Column(DateTime(timezone=True))
    cancelled_at    = Column(DateTime(timezone=True))
    cancel_reason   = Column(String(300))

    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    barber          = relationship("Barber", back_populates="appointments")
    client          = relationship("Client", back_populates="appointments")
    service         = relationship("Service", back_populates="appointments")

# ── Tabla: notifications ────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(Integer, primary_key=True)
    appointment_id  = Column(Integer, ForeignKey("appointments.id"))
    channel         = Column(String(20))    # "email", "sms", "push"
    type            = Column(String(30))    # "confirmation", "reminder_1h"
    status          = Column(String(20), default="pending")  # sent, failed
    sent_at         = Column(DateTime(timezone=True))
    error_message   = Column(Text)


# ─────────────────────────────────────────────────────────────
# 2. SCHEMAS PYDANTIC (validación de API)
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re

class CreateAppointmentRequest(BaseModel):
    barber_id:       int
    service_id:      int
    scheduled_at:    datetime           # ej: "2025-07-14T09:00:00-05:00"
    client_name:     str
    client_email:    EmailStr
    client_phone:    Optional[str] = None
    style_notes:     Optional[str] = None
    style_image_url: Optional[str] = None

    @field_validator("scheduled_at")
    @classmethod
    def must_be_on_the_hour(cls, v: datetime) -> datetime:
        if v.minute != 0 or v.second != 0:
            raise ValueError("Las citas deben comenzar en punto (minuto 00).")
        return v

    @field_validator("client_phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^\+?[\d\s\-]{7,15}$", v):
            raise ValueError("Número de teléfono inválido.")
        return v

class AppointmentResponse(BaseModel):
    id:               int
    confirmation_code:str
    barber_name:      str
    service_name:     str
    scheduled_at:     datetime
    ends_at:          datetime
    status:           str
    price_cop:        float

    class Config:
        from_attributes = True

class AvailabilityRequest(BaseModel):
    barber_id: int
    date:      str  # "2025-07-14"

class BarberStatusUpdate(BaseModel):
    status:        BarberStatus
    delay_minutes: int = 0


# ─────────────────────────────────────────────────────────────
# 3. SERVICIOS DE NEGOCIO
# ─────────────────────────────────────────────────────────────

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import timedelta
import secrets, string

SLOT_DURATION = timedelta(minutes=60)

def generate_confirmation_code() -> str:
    """Genera un código único tipo: BD-X7K2M9"""
    chars = string.ascii_uppercase + string.digits
    return "BD-" + "".join(secrets.choice(chars) for _ in range(6))

async def get_or_create_client(
    db: AsyncSession, name: str, email: str, phone: str | None
) -> Client:
    result = await db.execute(select(Client).where(Client.email == email))
    client = result.scalar_one_or_none()
    if not client:
        client = Client(name=name, email=email, phone=phone)
        db.add(client)
        await db.flush()
    return client

async def check_availability(
    db: AsyncSession, barber_id: int, scheduled_at: datetime
) -> bool:
    """
    Retorna True si el slot está disponible (anti double-booking).
    Un barbero no puede tener dos citas cuyo rango de tiempo se solape.
    """
    slot_end = scheduled_at + SLOT_DURATION
    conflict = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.barber_id == barber_id,
                Appointment.status.notin_([
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW,
                ]),
                Appointment.scheduled_at < slot_end,
                Appointment.ends_at   > scheduled_at,
            )
        )
    )
    return conflict.scalar_one_or_none() is None

async def get_barber_availability(
    db: AsyncSession, barber_id: int, date_str: str
) -> list[str]:
    """
    Devuelve lista de slots libres para un barbero en una fecha.
    Formato: ["08:00", "09:00", ...]
    """
    from datetime import date as date_type
    target_date = date_type.fromisoformat(date_str)
    day_of_week = target_date.weekday()  # 0=Lun

    # Verificar horario del barbero ese día
    sched_result = await db.execute(
        select(BarberSchedule).where(
            and_(
                BarberSchedule.barber_id == barber_id,
                BarberSchedule.day_of_week == day_of_week,
                BarberSchedule.is_active == True,
            )
        )
    )
    schedule = sched_result.scalar_one_or_none()
    if not schedule:
        return []

    # Generar todos los slots del día
    import pytz
    tz = pytz.timezone("America/Bogota")
    start_h = int(schedule.start_time.split(":")[0])
    end_h   = int(schedule.end_time.split(":")[0])

    all_slots = []
    for h in range(start_h, end_h):
        dt = datetime(target_date.year, target_date.month, target_date.day, h, 0, 0)
        all_slots.append(tz.localize(dt))

    # Filtrar ocupados
    available = []
    for slot in all_slots:
        if await check_availability(db, barber_id, slot):
            available.append(f"{slot.hour:02d}:00")
    return available


# ─────────────────────────────────────────────────────────────
# 4. NOTIFICACIONES (simulación con Celery + Redis)
# ─────────────────────────────────────────────────────────────

"""
Producción real usaría:
  • Email  → SendGrid / AWS SES
  • SMS    → Twilio
  • Push   → Firebase Cloud Messaging (FCM)
"""

from celery import Celery
import logging

logger = logging.getLogger("barberia.notifications")

celery_app = Celery(
    "barberia",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_confirmation_notification(self, appointment_id: int):
    """
    Disparado INMEDIATAMENTE al confirmar la cita.
    Envía Email + SMS de confirmación.
    """
    try:
        # En producción: consultar DB y enviar por SendGrid/Twilio
        logger.info(f"[NOTIF] Confirmación enviada → cita #{appointment_id}")
        _simulate_email(appointment_id, "confirmation")
        _simulate_sms(appointment_id, "confirmation")
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3)
def send_reminder_notification(self, appointment_id: int):
    """
    Disparado 1 hora ANTES de la cita vía Celery Beat (scheduler).
    """
    try:
        logger.info(f"[NOTIF] Recordatorio 1h → cita #{appointment_id}")
        _simulate_email(appointment_id, "reminder_1h")
        _simulate_sms(appointment_id, "reminder_1h")
        _simulate_push(appointment_id, "reminder_1h")
    except Exception as exc:
        raise self.retry(exc=exc)

def _simulate_email(appointment_id: int, notif_type: str):
    templates = {
        "confirmation": {
            "subject": "✂ Tu cita en Barbería Disruptiva está confirmada",
            "body": "Tu barbero ya vio tu perfil de estilo. Llega 5 min antes."
        },
        "reminder_1h": {
            "subject": "⏰ Tu cita es en 1 hora — Barbería Disruptiva",
            "body": "Revisa el check-in en vivo para saber si tu barbero va en horario."
        }
    }
    t = templates.get(notif_type, {})
    logger.info(f"  [EMAIL] '{t.get('subject')}' → cita #{appointment_id}")

def _simulate_sms(appointment_id: int, notif_type: str):
    msgs = {
        "confirmation": "Tu cita BD está confirmada. Código: ver email.",
        "reminder_1h":  "⏰ En 1h tu cita en BarberíaDisruptiva. Revisa el estado en vivo."
    }
    logger.info(f"  [SMS] '{msgs.get(notif_type)}' → cita #{appointment_id}")

def _simulate_push(appointment_id: int, notif_type: str):
    logger.info(f"  [PUSH] Recordatorio push → cita #{appointment_id}")

# Programar recordatorio al crear la cita:
def schedule_reminder(appointment_id: int, scheduled_at: datetime):
    reminder_time = scheduled_at - timedelta(hours=1)
    send_reminder_notification.apply_async(
        args=[appointment_id],
        eta=reminder_time
    )
    logger.info(f"[SCHEDULER] Recordatorio programado para {reminder_time.isoformat()}")


# ─────────────────────────────────────────────────────────────
# 5. ENDPOINTS FASTAPI
# ─────────────────────────────────────────────────────────────

import os  # Necesario para leer la variable de entorno
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# 1. Leemos la URL de Render. Si no existe (local), usamos la de desarrollo.
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Truco de compatibilidad: Render usa 'postgres://', pero SQLAlchemy requiere 'postgresql+asyncpg://'
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # URL de respaldo para cuando trabajes en tu PC
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost/barberia_db"

# 3. Configuración del motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

app = FastAPI(
    title="Barbería Disruptiva API",
    version="1.0.0",
    description="Sistema de agendamiento sin fricciones para barbería moderna."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://barberia-disruptiva.co"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with SessionLocal() as session:
        yield session

# ── GET /barbers ─────────────────────────────────────────────
@app.get("/barbers", summary="Listar todos los barberos activos")
async def list_barbers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Barber).where(Barber.is_active == True))
    return result.scalars().all()

# ── GET /barbers/{id}/availability ──────────────────────────
@app.get("/barbers/{barber_id}/availability", summary="Slots disponibles por fecha")
async def barber_availability(
    barber_id: int,
    date: str,
    db: AsyncSession = Depends(get_db)
):
    slots = await get_barber_availability(db, barber_id, date)
    return {"barber_id": barber_id, "date": date, "available_slots": slots}

# ── GET /barbers/{id}/live-status ───────────────────────────
@app.get("/barbers/{barber_id}/live-status", summary="Check-in digital en tiempo real")
async def barber_live_status(barber_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Barber).where(Barber.id == barber_id))
    barber = result.scalar_one_or_none()
    if not barber:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    delay = barber.delay_minutes
    return {
        "barber_id":     barber_id,
        "name":          barber.name,
        "status":        barber.status,
        "delay_minutes": delay,
        "message": (
            f"Va {abs(delay)} minutos adelantado 🟢" if delay < 0 else
            "En horario exacto 🟡" if delay == 0 else
            f"Lleva {delay} minutos de retraso 🟠"
        )
    }

# ── POST /appointments ───────────────────────────────────────
@app.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita (endpoint principal)"
)
async def create_appointment(
    payload: CreateAppointmentRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar que el barbero exista y esté activo
    barber_result = await db.execute(
        select(Barber).where(Barber.id == payload.barber_id, Barber.is_active == True)
    )
    barber = barber_result.scalar_one_or_none()
    if not barber:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    # 2. Verificar que el servicio exista
    service_result = await db.execute(
        select(Service).where(Service.id == payload.service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")

    # 3. Anti double-booking — verificar disponibilidad
    available = await check_availability(db, payload.barber_id, payload.scheduled_at)
    if not available:
        raise HTTPException(
            status_code=409,
            detail="Este horario ya está ocupado con otro cliente. Elige otro slot."
        )

    # 4. Obtener o crear cliente
    client = await get_or_create_client(
        db, payload.client_name, payload.client_email, payload.client_phone
    )

    # 5. Crear la cita
    ends_at = payload.scheduled_at + SLOT_DURATION
    code    = generate_confirmation_code()

    appointment = Appointment(
        barber_id        = payload.barber_id,
        client_id        = client.id,
        service_id       = payload.service_id,
        scheduled_at     = payload.scheduled_at,
        ends_at          = ends_at,
        status           = AppointmentStatus.CONFIRMED,
        style_notes      = payload.style_notes,
        style_image_url  = payload.style_image_url,
        price_paid       = service.price_cop,
        confirmation_code= code,
        confirmed_at     = datetime.utcnow(),
    )
    db.add(appointment)
    client.total_visits += 1
    await db.commit()
    await db.refresh(appointment)

    # 6. Disparar notificaciones asíncronas
    send_confirmation_notification.delay(appointment.id)
    schedule_reminder(appointment.id, payload.scheduled_at)

    return AppointmentResponse(
        id                = appointment.id,
        confirmation_code = code,
        barber_name       = barber.name,
        service_name      = service.name,
        scheduled_at      = appointment.scheduled_at,
        ends_at           = appointment.ends_at,
        status            = appointment.status,
        price_cop         = float(service.price_cop),
    )

# ── PATCH /barbers/{id}/status (uso interno de barberos) ────
@app.patch("/barbers/{barber_id}/status", summary="Actualizar estado del barbero en tiempo real")
async def update_barber_status(
    barber_id: int,
    payload: BarberStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Barber).where(Barber.id == barber_id))
    barber = result.scalar_one_or_none()
    if not barber:
        raise HTTPException(status_code=404, detail="Barbero no encontrado.")
    barber.status = payload.status
    barber.delay_minutes = payload.delay_minutes
    await db.commit()
    return {"message": "Estado actualizado", "delay_minutes": payload.delay_minutes}

# ── DELETE /appointments/{id} ────────────────────────────────
@app.delete("/appointments/{appointment_id}", summary="Cancelar una cita")
async def cancel_appointment(
    appointment_id: int,
    reason: str = "Sin especificar",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    if appt.status == AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="La cita ya fue cancelada.")
    appt.status = AppointmentStatus.CANCELLED
    appt.cancelled_at = datetime.utcnow()
    appt.cancel_reason = reason
    await db.commit()
    return {"message": "Cita cancelada exitosamente.", "appointment_id": appointment_id}


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
