from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenRouterClientError(RuntimeError):
    """Raised when categorization using OpenRouter fails."""


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        base_url: str,
        site_url: str | None = None,
        app_name: str = "financebot",
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url
        self.site_url = site_url
        self.app_name = app_name

    def categorize(self, description: str, categories: list[str]) -> str | None:
        normalized_categories = [category.strip().lower() for category in categories if category.strip()]
        if not normalized_categories:
            return None

        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 40,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Clasifica gastos personales. "
                        "Responde unicamente JSON con estructura exacta: {\"category\":\"valor\"}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Descripcion: {description}\n"
                        f"Categorias permitidas: {', '.join(sorted(set(normalized_categories)))}"
                    ),
                },
            ],
        }

        response_payload = self._send(payload)
        content = self._extract_message_content(response_payload)
        category = self._extract_category(content)
        if category in set(normalized_categories):
            return category
        return None

    def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        body = json.dumps(payload).encode("utf-8")
        request = Request(self.base_url, data=body, headers=headers, method="POST")

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                return json.loads(raw_body)
        except HTTPError as error:
            raise OpenRouterClientError(f"OpenRouter respondio con estado HTTP {error.code}") from error
        except URLError as error:
            raise OpenRouterClientError(f"No se pudo conectar a OpenRouter: {error.reason}") from error
        except json.JSONDecodeError as error:
            raise OpenRouterClientError("OpenRouter devolvio una respuesta no JSON") from error

    @staticmethod
    def _extract_message_content(response_payload: dict[str, Any]) -> str:
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterClientError("Respuesta invalida de OpenRouter: choices ausente")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterClientError("Respuesta invalida de OpenRouter: choice invalido")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterClientError("Respuesta invalida de OpenRouter: message ausente")

        content = message.get("content")
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_fragments: list[str] = []
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("type") == "text" and isinstance(chunk.get("text"), str):
                    text_fragments.append(chunk["text"])
            if text_fragments:
                return "\n".join(text_fragments)

        raise OpenRouterClientError("Respuesta invalida de OpenRouter: content ausente")

    @staticmethod
    def _extract_category(content: str) -> str | None:
        stripped = content.strip()
        if not stripped:
            return None

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped.lower()

        if not isinstance(payload, dict):
            return None

        category = payload.get("category")
        if not isinstance(category, str):
            return None

        normalized = category.strip().lower()
        return normalized or None
