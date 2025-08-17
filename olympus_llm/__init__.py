# Shim for local imports without installation
from packages.llm.olympus_llm.router import LLMRouter, ModelNotAllowedError, BudgetExceeded

__all__ = ["LLMRouter", "ModelNotAllowedError", "BudgetExceeded"]

