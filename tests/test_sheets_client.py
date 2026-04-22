from finance_bot.sheets_client import SheetsExpenseWriter


def test_sheet_reference_escapes_single_quotes() -> None:
    reference = SheetsExpenseWriter._sheet_reference("expenses'2026")
    assert reference == "'expenses''2026'"


def test_build_category_chart_request_has_expected_title() -> None:
    request = SheetsExpenseWriter._build_category_pie_chart_request(123)
    assert request["addChart"]["chart"]["spec"]["title"] == "Gasto por categoria"


def test_build_monthly_chart_request_has_expected_title() -> None:
    request = SheetsExpenseWriter._build_monthly_column_chart_request(456)
    assert request["addChart"]["chart"]["spec"]["title"] == "Tendencia mensual"
