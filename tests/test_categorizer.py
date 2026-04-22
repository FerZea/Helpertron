from finance_bot.categorizer import RuleCategorizer


class StubAICategorizer:
    def __init__(self, result: str | None, should_raise: bool = False):
        self.result = result
        self.should_raise = should_raise

    def categorize(self, description: str, categories: list[str]) -> str | None:
        if self.should_raise:
            raise RuntimeError("network failure")
        return self.result


def test_categorize_matches_keyword() -> None:
    categorizer = RuleCategorizer(rules={"uber": "transporte", "oxxo": "comida"})
    assert categorizer.categorize("Uber 200") == "transporte"


def test_categorize_uses_default_when_no_match() -> None:
    categorizer = RuleCategorizer(rules={"uber": "transporte"}, default_category="otros")
    assert categorizer.categorize("Farmacia 100") == "otros"


def test_add_and_delete_rule() -> None:
    categorizer = RuleCategorizer()
    categorizer.add_rule("NETFLIX", "entretenimiento")
    assert categorizer.categorize("Netflix 199") == "entretenimiento"

    deleted = categorizer.delete_rule("netflix")
    assert deleted is True
    assert categorizer.categorize("Netflix 199") == "otros"


def test_categorize_uses_ai_fallback_when_no_rule_matches() -> None:
    categorizer = RuleCategorizer(
        rules={"uber": "transporte"},
        default_category="otros",
        ai_categorizer=StubAICategorizer(result="comida"),
        ai_categories=["comida", "transporte", "otros"],
    )

    assert categorizer.categorize("Sushi 240") == "comida"


def test_categorize_falls_back_to_default_when_ai_fails() -> None:
    categorizer = RuleCategorizer(
        rules={"uber": "transporte"},
        default_category="otros",
        ai_categorizer=StubAICategorizer(result=None, should_raise=True),
        ai_categories=["comida", "transporte", "otros"],
    )

    assert categorizer.categorize("Sushi 240") == "otros"
