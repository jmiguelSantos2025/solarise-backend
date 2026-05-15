import hashlib
import uuid
from datetime import date, datetime, timezone
from typing import Optional
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
    contratos: list['Contrato'] = Relationship(back_populates='organization')


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id:              uuid.UUID     = Field(default_factory=uuid.uuid4, primary_key=True)
    email:           str           = Field(max_length=255, unique=True)
    name:            str           = Field(max_length=255)
    role:            str           = Field(default='user', max_length=50)
    organization_id: uuid.UUID     = Field(foreign_key='organizations.id')
    created_at:      datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:      datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))

    organization: Optional[Organization] = Relationship(back_populates='users')


class Contrato(SQLModel, table=True):
    __tablename__ = 'contratos'

    id:              uuid.UUID        = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID        = Field(foreign_key='organizations.id')
    number:          str              = Field(max_length=100, unique=True)
    description:     Optional[str]    = Field(default=None)
    start_date:      date
    end_date:        Optional[date]   = Field(default=None)
    value_kwh:       float            = Field(decimal_places=4)
    status:          str              = Field(default='active', max_length=50)
    created_at:      datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:      datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))

    organization: Optional[Organization]    = Relationship(back_populates='contratos')
    geracoes:     list['GeracaoEnergia']    = Relationship(back_populates='contrato')


class GeracaoEnergia(SQLModel, table=True):
    __tablename__ = 'geracao_energia'

    id:              uuid.UUID      = Field(default_factory=uuid.uuid4, primary_key=True)
    contrato_id:     uuid.UUID      = Field(foreign_key='contratos.id')
    organization_id: uuid.UUID      = Field(foreign_key='organizations.id')
    periodo_ref:     date
    energia_kwh:     float          = Field(decimal_places=4)
    fonte:           Optional[str]  = Field(default=None, max_length=100)
    hash_sha256:     str            = Field(max_length=64, unique=True)
    hash_anterior:   Optional[str]  = Field(default=None, max_length=64)
    created_at:      datetime       = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by:      Optional[uuid.UUID] = Field(default=None, foreign_key='users.id')

    contrato:   Optional[Contrato] = Relationship(back_populates='geracoes')


def calcular_hash(geracao: GeracaoEnergia) -> str:
    payload = (
        f"{geracao.id}"
        f"{geracao.contrato_id}"
        f"{geracao.periodo_ref}"
        f"{geracao.energia_kwh}"
        f"{geracao.hash_anterior or ''}"
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

