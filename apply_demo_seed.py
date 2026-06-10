"""
Script: aplica os dados de demo sem apagar o banco existente.
Só insere se o usuário instaladora@solartech.am ainda não existir.
Rode com: railway run python apply_demo_seed.py
"""
import hashlib
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from passlib.context import CryptContext
from sqlmodel import Session, select

from database.database import engine
from database.models import Contract, EnergyGeneration, Organization, User

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_EMAIL     = "instaladora@solartech.am"
DEMO_PASSWORD  = "solarize2026"
DEMO_ORG_CNPJ  = "12345678000199"


def _calculate_hash(gen_id, contract_id, reference_period, energy_kwh, previous_hash):
    payload = (
        f"{gen_id}"
        f"{contract_id}"
        f"{reference_period}"
        f"{energy_kwh:.6f}"
        f"{previous_hash or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run():
    with Session(engine) as session:
        # Verifica se o usuário demo já existe
        existing = session.exec(select(User).where(User.email == DEMO_EMAIL)).first()
        if existing:
            print(f"Usuário {DEMO_EMAIL} já existe — abortando.")
            return

        print("Aplicando dados de demo...")

        # Busca ou cria a organização pelo CNPJ
        org = session.exec(select(Organization).where(Organization.cnpj == DEMO_ORG_CNPJ)).first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="SolarTech AM",
                cnpj=DEMO_ORG_CNPJ,
                email="contato@solartech.am",
                active=True,
            )
            session.add(org)
            session.flush()
            print(f"  Organização criada: SolarTech AM (id={str(org.id)[:8]}...)")
        else:
            print(f"  Organização já existe: {org.name} — reutilizando.")

        # Cria usuário instaladora
        user_instaladora = User(
            id=uuid.uuid4(),
            email=DEMO_EMAIL,
            name="Admin SolarTech",
            role="instaladora",
            organization_id=org.id,
            password_hash=_pwd.hash(DEMO_PASSWORD),
        )
        session.add(user_instaladora)

        # Cria usuário locador
        user_locador = User(
            id=uuid.uuid4(),
            email="joaosilva@locador.com",
            name="Joao Silva",
            role="locador",
            organization_id=org.id,
            password_hash=_pwd.hash(DEMO_PASSWORD),
        )
        session.add(user_locador)
        session.flush()
        print(f"  Usuários criados: {DEMO_EMAIL} e joaosilva@locador.com")

        # Verifica se o contrato CONT-001 já existe nessa org
        contract = session.exec(
            select(Contract).where(
                Contract.number == "CONT-001",
                Contract.organization_id == org.id,
            )
        ).first()
        if not contract:
            contract_id = uuid.uuid4()
            contract = Contract(
                id=contract_id,
                organization_id=org.id,
                number="CONT-001",
                description="Galpao 500m2 - Joao Silva",
                start_date=date(2026, 1, 1),
                value_kwh=Decimal("0.85"),
                landlord_percentage=Decimal("0.30"),
                status="active",
            )
            session.add(contract)
            session.flush()
            print(f"  Contrato criado: CONT-001 (id={str(contract.id)[:8]}...)")
        else:
            print(f"  Contrato CONT-001 já existe — reutilizando.")

        # Verifica se já existem gerações para esse contrato
        existing_gen = session.exec(
            select(EnergyGeneration).where(EnergyGeneration.contract_id == contract.id)
        ).first()
        if existing_gen:
            print("  Gerações já existem — pulando inserção de gerações.")
        else:
            months = [
                (date(2026, 1, 1), Decimal("36200")),
                (date(2026, 2, 1), Decimal("34850")),
                (date(2026, 3, 1), Decimal("38500")),
            ]
            previous_hash = None
            for reference_period, energy_kwh in months:
                gen_id = uuid.uuid4()
                hash_now = _calculate_hash(gen_id, contract.id, reference_period, energy_kwh, previous_hash)
                valor = (
                    energy_kwh * Decimal("0.85") * Decimal("0.30") * Decimal("0.95")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                session.add(EnergyGeneration(
                    id=gen_id,
                    contract_id=contract.id,
                    organization_id=org.id,
                    reference_period=reference_period,
                    energy_kwh=energy_kwh,
                    hash_sha256=hash_now,
                    previous_hash=previous_hash,
                    created_by=user_instaladora.id,
                ))
                previous_hash = hash_now
                print(f"  Geração {reference_period}: {energy_kwh} kWh = R$ {valor} | hash: {hash_now[:16]}...")

        session.commit()
        print("\nDados de demo aplicados com sucesso!")
        print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Login: joaosilva@locador.com / {DEMO_PASSWORD}")


if __name__ == "__main__":
    run()
