from decimal import Decimal, ROUND_HALF_UP

def landlord_calculator(energy: Decimal, tariff: Decimal, percentage: Decimal) -> Decimal: #Implementar hash no futuro
    loss_factor = Decimal("0.95")
    value = loss_factor*energy*tariff*percentage
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)