from typing import Dict


class BudgetManager:
    def __init__(self, budgets: Dict[str, Dict[str, float]]):
        self.budgets = budgets  # e.g. {"openai": {"tokens": 1000000, "cost_usd": 10.0}}

    def check_budget(self, provider: str, tokens: int, cost_usd: float) -> bool:
        if provider not in self.budgets:
            return True  # No budget for this provider
        return (
            self.budgets[provider]["tokens"] >= tokens
            and self.budgets[provider]["cost_usd"] >= cost_usd
        )

    def update_budget(self, provider: str, tokens: int, cost_usd: float):
        if provider in self.budgets:
            self.budgets[provider]["tokens"] -= tokens
            self.budgets[provider]["cost_usd"] -= cost_usd
