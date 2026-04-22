from __future__ import annotations

from pathlib import Path
from typing import Any

import gspread
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
from gspread.spreadsheet import Spreadsheet
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
    def __init__(
        self,
        spreadsheet_id: str,
        service_account_file: Path,
        worksheet_name: str = "expenses",
        dashboard_worksheet_name: str = "dashboard",
    ):
        self.spreadsheet_id = spreadsheet_id
        self.service_account_file = service_account_file
        self.worksheet_name = worksheet_name
        self.dashboard_worksheet_name = dashboard_worksheet_name
        self._spreadsheet: Spreadsheet | None = None
        self._worksheet: Worksheet | None = None

    def append_expense(self, expense: ExpenseRecord) -> None:
        worksheet = self._get_worksheet()
        worksheet.append_row(expense.to_sheet_row(), value_input_option="USER_ENTERED")

    def _get_worksheet(self) -> Worksheet:
        if self._worksheet is not None:
            return self._worksheet

        spreadsheet = self._get_spreadsheet()

        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
        except WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=10)

        self._ensure_headers(worksheet)
        self._ensure_dashboard(spreadsheet=spreadsheet, expense_worksheet=worksheet)
        self._worksheet = worksheet
        return worksheet

    def _get_spreadsheet(self) -> Spreadsheet:
        if self._spreadsheet is not None:
            return self._spreadsheet

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

        self._spreadsheet = spreadsheet
        return spreadsheet

    def _ensure_headers(self, worksheet: Worksheet) -> None:
        first_row = worksheet.row_values(1)
        if first_row[: len(SHEET_HEADERS)] != SHEET_HEADERS:
            worksheet.update("A1:G1", [SHEET_HEADERS])

    def _ensure_dashboard(self, spreadsheet: Spreadsheet, expense_worksheet: Worksheet) -> None:
        try:
            dashboard = spreadsheet.worksheet(self.dashboard_worksheet_name)
        except WorksheetNotFound:
            dashboard = spreadsheet.add_worksheet(title=self.dashboard_worksheet_name, rows=1000, cols=20)

        dashboard.update("A1:B1", [["categoria", "total"]])
        dashboard.update("D1:E1", [["mes", "total"]])

        expense_sheet_ref = self._sheet_reference(expense_worksheet.title)
        category_formula = (
            f"=QUERY({expense_sheet_ref}!A:G,"
            '"select E, sum(D) where E is not null group by E label sum(D) \'\'",1)'
        )
        monthly_formula = (
            f"=QUERY({{ARRAYFORMULA(LEFT({expense_sheet_ref}!B2:B,7)),{expense_sheet_ref}!D2:D}},"
            '"select Col1, sum(Col2) where Col1 is not null group by Col1 order by Col1 label sum(Col2) \'\'",0)'
        )

        dashboard.update("A2", [[category_formula]], value_input_option="USER_ENTERED")
        dashboard.update("D2", [[monthly_formula]], value_input_option="USER_ENTERED")
        self._ensure_charts(spreadsheet=spreadsheet, dashboard=dashboard)

    def _ensure_charts(self, spreadsheet: Spreadsheet, dashboard: Worksheet) -> None:
        existing_titles = self._existing_chart_titles(spreadsheet)
        requests: list[dict[str, Any]] = []

        if "Gasto por categoria" not in existing_titles:
            requests.append(self._build_category_pie_chart_request(dashboard.id))

        if "Tendencia mensual" not in existing_titles:
            requests.append(self._build_monthly_column_chart_request(dashboard.id))

        if requests:
            spreadsheet.batch_update({"requests": requests})

    @staticmethod
    def _sheet_reference(sheet_title: str) -> str:
        escaped = sheet_title.replace("'", "''")
        return f"'{escaped}'"

    @staticmethod
    def _existing_chart_titles(spreadsheet: Spreadsheet) -> set[str]:
        metadata = spreadsheet.fetch_sheet_metadata()
        titles: set[str] = set()
        for sheet in metadata.get("sheets", []):
            for chart in sheet.get("charts", []):
                spec = chart.get("spec", {})
                title = spec.get("title")
                if isinstance(title, str) and title.strip():
                    titles.add(title.strip())
        return titles

    @staticmethod
    def _build_category_pie_chart_request(sheet_id: int) -> dict[str, Any]:
        return {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Gasto por categoria",
                        "pieChart": {
                            "legendPosition": "RIGHT_LEGEND",
                            "domain": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 500,
                                            "startColumnIndex": 0,
                                            "endColumnIndex": 1,
                                        }
                                    ]
                                }
                            },
                            "series": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 500,
                                            "startColumnIndex": 1,
                                            "endColumnIndex": 2,
                                        }
                                    ]
                                }
                            },
                        },
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 6},
                            "offsetXPixels": 0,
                            "offsetYPixels": 0,
                            "widthPixels": 650,
                            "heightPixels": 420,
                        }
                    },
                }
            }
        }

    @staticmethod
    def _build_monthly_column_chart_request(sheet_id: int) -> dict[str, Any]:
        return {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Tendencia mensual",
                        "basicChart": {
                            "chartType": "COLUMN",
                            "legendPosition": "NO_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Mes"},
                                {"position": "LEFT_AXIS", "title": "Monto"},
                            ],
                            "domains": [
                                {
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [
                                                {
                                                    "sheetId": sheet_id,
                                                    "startRowIndex": 1,
                                                    "endRowIndex": 500,
                                                    "startColumnIndex": 3,
                                                    "endColumnIndex": 4,
                                                }
                                            ]
                                        }
                                    }
                                }
                            ],
                            "series": [
                                {
                                    "series": {
                                        "sourceRange": {
                                            "sources": [
                                                {
                                                    "sheetId": sheet_id,
                                                    "startRowIndex": 1,
                                                    "endRowIndex": 500,
                                                    "startColumnIndex": 4,
                                                    "endColumnIndex": 5,
                                                }
                                            ]
                                        }
                                    }
                                }
                            ],
                            "headerCount": 0,
                        },
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {"sheetId": sheet_id, "rowIndex": 22, "columnIndex": 6},
                            "offsetXPixels": 0,
                            "offsetYPixels": 0,
                            "widthPixels": 650,
                            "heightPixels": 420,
                        }
                    },
                }
            }
        }
