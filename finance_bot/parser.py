from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


EXPENSE_PATTERN = re.compile(
    r"^\s*(?P<description>.+?)\s+(?P<amount>[+-]?\d+(?:[\.,]\d{1,2})?)\s*$"
)


class ParseExpenseError(ValueError):
    """Raised when a Telegram message cannot be parsed as an expense."""


def parse_expense_text(text: str) -> tuple[str, Decimal]:
    match = EXPENSE_PATTERN.match(text)
    if not match:
        raise ParseExpenseError("Formato invalido. Usa: Descripcion monto (ej. Uber 200)")

    description = " ".join(match.group("description").split())
    raw_amount = match.group("amount").replace(",", ".")

    try:
        amount = Decimal(raw_amount)
    except InvalidOperation as error:
        raise ParseExpenseError("No se pudo interpretar el monto.") from error

    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= Decimal("0"):
        raise ParseExpenseError("El monto debe ser mayor a 0.")

    return description, amount
