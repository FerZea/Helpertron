from decimal import Decimal

import pytest

from finance_bot.parser import ParseExpenseError, parse_expense_text


def test_parse_expense_text_valid() -> None:
    description, amount = parse_expense_text("Uber 200")
    assert description == "Uber"
    assert amount == Decimal("200.00")


def test_parse_expense_text_valid_comma_decimal() -> None:
    description, amount = parse_expense_text("Cafe 45,5")
    assert description == "Cafe"
    assert amount == Decimal("45.50")


@pytest.mark.parametrize(
    "raw_text",
    [
        "",
        "SoloTexto",
        "Uber -20",
        "Uber 0",
    ],
)
def test_parse_expense_text_invalid(raw_text: str) -> None:
    with pytest.raises(ParseExpenseError):
        parse_expense_text(raw_text)
