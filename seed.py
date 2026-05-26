import hashlib
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from passlib.context import CryptContext
from sqlmodel import Session, select

from database.database import engine
from database.models import Contract, EnergyGeneration, Organization, User

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _calculate_hash(gen_id, contract_id, reference_period, energy_kwh, previous_hash):
    payload = (
        f"{gen_id}"
        f"{contract_id}"
        f"{reference_period}"
        f"{energy_kwh:.6f}"
        f"{previous_hash or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_seed():
    with Session(engine) as session:
        if session.exec(select(Organization)).first():
            print("Seed já aplicado — abortando.")
            return

        print("Aplicando seed...")

        org_id = uuid.uuid4()
        org = Organization(
            id=org_id,
            name="SolarTech AM",
            cnpj="12.345.678/0001-99",
            email="contato@solartech.am",
            active=True,
        )
        session.add(org)

        session.add(User(
            id=uuid.uuid4(),
            email="instaladora@solartech.am",
            name="Admin SolarTech",
            role="instaladora",
            organization_id=org_id,
            password_hash=_pwd.hash("solarize2026"),
        ))

        session.add(User(
            id=uuid.uuid4(),
            email="joaosilva@locador.com",
            name="Joao Silva",
            role="locador",
            organization_id=org_id,
            password_hash=_pwd.hash("solarize2026"),
        ))

        contract_id = uuid.uuid4()
        session.add(Contract(
            id=contract_id,
            organization_id=org_id,
            number="CONT-001",
            description="Galpao 500m2 - Joao Silva",
            start_date=date(2026, 1, 1),
            value_kwh=Decimal("0.85"),
            landlord_percentage=Decimal("0.30"),
            status="active",
        ))
        session.flush()

        months = [
            (date(2026, 1, 1), Decimal("36200")),
            (date(2026, 2, 1), Decimal("34850")),
            (date(2026, 3, 1), Decimal("38500")),
        ]

        previous_hash = None
        for reference_period, energy_kwh in months:
            gen_id = uuid.uuid4()
            hash_now = _calculate_hash(gen_id, contract_id, reference_period, energy_kwh, previous_hash)
            valor = (
                energy_kwh * Decimal("0.85") * Decimal("0.30") * Decimal("0.95")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            session.add(EnergyGeneration(
                id=gen_id,
                contract_id=contract_id,
                organization_id=org_id,
                reference_period=reference_period,
                energy_kwh=energy_kwh,
                hash_sha256=hash_now,
                previous_hash=previous_hash,
            ))
            previous_hash = hash_now
            print(f"  {reference_period}: {energy_kwh} kWh = R${valor} | hash: {hash_now[:16]}...")

        session.commit()
        print("Seed aplicado com sucesso!")
        print("  jan/26: 36.200 kWh = R$ 8.777,55")
        print("  fev/26: 34.850 kWh = R$ 8.452,16")
        print("  mar/26: 38.500 kWh = R$ 9.325,50")


if __name__ == "__main__":
    run_seed()
