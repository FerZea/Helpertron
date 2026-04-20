from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class ExpenseRecord:
    description: str
    amount: Decimal
    category: str
    currency: str
    timestamp_utc: datetime
    timestamp_local: datetime
    telegram_message_id: int

    def to_sheet_row(self) -> list[str]:
        return [
            self.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            self.timestamp_local.strftime("%Y-%m-%d %H:%M:%S"),
            self.description,
            format(self.amount, "f"),
            self.category,
            self.currency,
            str(self.telegram_message_id),
        ]
