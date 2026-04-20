from __future__ import annotations

from pathlib import Path

import gspread
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
from gspread.worksheet import Worksheet

from finance_bot.models import ExpenseRecord

SHEET_HEADERS = [
    "timestamp_utc",
    "timestamp_local",
    "descripcion",
    "monto",
    "categoria",
    "moneda",
    "telegram_message_id",
]


class SheetsClientError(RuntimeError):
    """Raised when reading or writing Google Sheets fails."""


class SheetsExpenseWriter:
    def __init__(self, spreadsheet_id: str, service_account_file: Path, worksheet_name: str = "expenses"):
        self.spreadsheet_id = spreadsheet_id
        self.service_account_file = service_account_file
        self.worksheet_name = worksheet_name
        self._worksheet: Worksheet | None = None

    def append_expense(self, expense: ExpenseRecord) -> None:
        worksheet = self._get_worksheet()
        worksheet.append_row(expense.to_sheet_row(), value_input_option="USER_ENTERED")

    def _get_worksheet(self) -> Worksheet:
        if self._worksheet is not None:
            return self._worksheet

        if not self.service_account_file.exists():
            raise SheetsClientError(
                f"No existe el archivo de credenciales de Google: {self.service_account_file}"
            )

        try:
            client = gspread.service_account(filename=str(self.service_account_file))
            spreadsheet = client.open_by_key(self.spreadsheet_id)
        except SpreadsheetNotFound as error:
            raise SheetsClientError(
                "No se encontro la hoja. Verifica GOOGLE_SHEETS_ID y permisos de la cuenta de servicio."
            ) from error
        except Exception as error:  # noqa: BLE001
            raise SheetsClientError(f"No se pudo autenticar con Google Sheets: {error}") from error

        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
        except WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=10)

        self._ensure_headers(worksheet)
        self._worksheet = worksheet
        return worksheet

    def _ensure_headers(self, worksheet: Worksheet) -> None:
        first_row = worksheet.row_values(1)
        if first_row[: len(SHEET_HEADERS)] != SHEET_HEADERS:
            worksheet.update("A1:G1", [SHEET_HEADERS])
