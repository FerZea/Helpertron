from finance_bot.openrouter_client import OpenRouterClient


class StubOpenRouterClient(OpenRouterClient):
    def __init__(self, response_payload: dict):
        super().__init__(
            api_key="test-key",
            model="openai/gpt-4o-mini",
            timeout_seconds=5,
            base_url="https://openrouter.ai/api/v1/chat/completions",
        )
        self.response_payload = response_payload

    def _send(self, payload: dict):  # type: ignore[override]
        return self.response_payload


def test_categorize_parses_json_category() -> None:
    client = StubOpenRouterClient(
        response_payload={
            "choices": [
                {
                    "message": {
                        "content": '{"category":"comida"}',
                    }
                }
            ]
        }
    )

    category = client.categorize("Sushi 230", ["comida", "transporte", "otros"])
    assert category == "comida"


def test_categorize_returns_none_when_category_not_allowed() -> None:
    client = StubOpenRouterClient(
        response_payload={
            "choices": [
                {
                    "message": {
                        "content": '{"category":"invalida"}',
                    }
                }
            ]
        }
    )

    category = client.categorize("Algo 100", ["comida", "transporte", "otros"])
    assert category is None


def test_categorize_accepts_plain_text_fallback() -> None:
    client = StubOpenRouterClient(
        response_payload={
            "choices": [
                {
                    "message": {
                        "content": "transporte",
                    }
                }
            ]
        }
    )

    category = client.categorize("Taxi 180", ["comida", "transporte", "otros"])
    assert category == "transporte"
