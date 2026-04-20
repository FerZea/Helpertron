from finance_bot.categorizer import RuleCategorizer


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
