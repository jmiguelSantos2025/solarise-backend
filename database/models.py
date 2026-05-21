import hashlib
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
<<<<<<< HEAD

from sqlalchemy import Column, Numeric
=======
from sqlalchemy import UniqueConstraint
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7
from sqlmodel import SQLModel, Field, Relationship


class Organization(SQLModel, table=True):
    __tablename__ = 'organizations'

    id:         uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    name:       str                 = Field(max_length=255, unique=True)
    cnpj:       str                 = Field(max_length=18, unique=True)
    email:      str                 = Field(max_length=255)
    phone:      Optional[str]       = Field(default=None, max_length=30)
    address:    Optional[str]       = Field(default=None)
    active:     bool                = Field(default=True)
    created_at: datetime            = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime            = Field(default_factory=lambda: datetime.now(timezone.utc))

    users:     list['User']     = Relationship(back_populates='organization')
    contracts: list['Contract'] = Relationship(back_populates='organization')


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id:              uuid.UUID     = Field(default_factory=uuid.uuid4, primary_key=True)
    email:           str           = Field(max_length=255, unique=True)
    name:            str           = Field(max_length=255)
    role:            str           = Field(default='user', max_length=50)
    organization_id: uuid.UUID     = Field(foreign_key='organizations.id')
    created_at:      datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:      datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))
    password_hash:   Optional[str] = Field(default=None, max_length=255)

    organization: Optional[Organization] = Relationship(back_populates='users')


<<<<<<< HEAD
class Contract(SQLModel, table=True):
    __tablename__ = 'contracts'

    id:                 uuid.UUID        = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id:    uuid.UUID        = Field(foreign_key='organizations.id')
    number:             str              = Field(max_length=100, unique=True)
    description:        Optional[str]    = Field(default=None)
    start_date:         date
    end_date:           Optional[date]   = Field(default=None)
    value_kwh:          Decimal          = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    landlord_percentage: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(5, 4), nullable=True))
    status:             str              = Field(default='active', max_length=50)
    created_at:         datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:         datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))

    organization: Optional[Organization]  = Relationship(back_populates='contracts')
    generations:  list['EnergyGeneration'] = Relationship(back_populates='contract')
=======
class Contrato(SQLModel, table=True):
    __tablename__ = 'contratos'
    __table_args__ = (UniqueConstraint("organization_id", "number", name="uq_contrato_org_number"),)

    id:              uuid.UUID        = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID        = Field(foreign_key='organizations.id')
    number:          str              = Field(max_length=100)
    description:     Optional[str]    = Field(default=None)
    start_date:      date
    end_date:        Optional[date]   = Field(default=None)
    value_kwh:       float            = Field(decimal_places=4)
    percentual_locador: Optional[float] = Field(default=None, decimal_places=4)
    status:          str              = Field(default='active', max_length=50)
    created_at:      datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:      datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7


class EnergyGeneration(SQLModel, table=True):
    __tablename__ = 'energy_generation'

    id:               uuid.UUID      = Field(default_factory=uuid.uuid4, primary_key=True)
    contract_id:      uuid.UUID      = Field(foreign_key='contracts.id')
    organization_id:  uuid.UUID      = Field(foreign_key='organizations.id')
    reference_period: date
    energy_kwh:       Decimal        = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    source:           Optional[str]  = Field(default=None, max_length=100)
    hash_sha256:      str            = Field(max_length=64, unique=True)
    previous_hash:    Optional[str]  = Field(default=None, max_length=64)
    created_at:       datetime       = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by:       Optional[uuid.UUID] = Field(default=None, foreign_key='users.id')

    contract: Optional[Contract] = Relationship(back_populates='generations')


def calculate_hash(generation: EnergyGeneration) -> str:
    payload = (
        f"{generation.id}"
        f"{generation.contract_id}"
        f"{generation.reference_period}"
        f"{generation.energy_kwh:.6f}"
        f"{generation.previous_hash or ''}"
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
