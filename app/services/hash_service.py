from decimal import Decimal, ROUND_HALF_UP

def landlord_calculator(energy: Decimal, tariff: float, percentage: float) -> Decimal: #Implementar hash no futuro
    loss_factor = Decimal("0.95")
    value = loss_factor*energy*Decimal(tariff)*Decimal(percentage)
    return value.quantize(Decimal(value), rounding=ROUND_HALF_UP)