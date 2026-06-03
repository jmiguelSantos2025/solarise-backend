from decimal import Decimal, ROUND_HALF_UP


def landlord_calculator(energy: Decimal, tariff: Decimal, percentage: Decimal) -> Decimal:
    loss_factor = Decimal("0.95")
    value = loss_factor * energy * Decimal(tariff) * Decimal(percentage)
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
