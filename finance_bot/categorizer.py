from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuleCategorizer:
    rules: dict[str, str] = field(default_factory=dict)
    default_category: str = "otros"

    def categorize(self, description: str) -> str:
        normalized_description = description.lower()

        for keyword in sorted(self.rules.keys(), key=len, reverse=True):
            if keyword and keyword in normalized_description:
                return self.rules[keyword]
        return self.default_category

    def add_rule(self, keyword: str, category: str) -> None:
        keyword_normalized = keyword.strip().lower()
        category_normalized = category.strip().lower()
        if not keyword_normalized:
            raise ValueError("La palabra clave no puede estar vacia")
        if not category_normalized:
            raise ValueError("La categoria no puede estar vacia")
        self.rules[keyword_normalized] = category_normalized

    def delete_rule(self, keyword: str) -> bool:
        keyword_normalized = keyword.strip().lower()
        if keyword_normalized in self.rules:
            del self.rules[keyword_normalized]
            return True
        return False
