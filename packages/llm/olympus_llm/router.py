import os
from typing import Any, AsyncGenerator, Dict, List, Optional
import yaml
from .providers import LLMProvider, OllamaProvider
from .budget import BudgetManager

class ModelNotAllowedError(Exception):
    status_code = 400

    def __init__(self, model: str) -> None:
        super().__init__(f"model not allowlisted: {model}")
        self.model = model


class ModelUnavailableError(Exception):
    status_code = 424

    def __init__(self, model: str, detail: str) -> None:
        super().__init__(detail)
        self.model = model
        self.detail = detail


class LLMRouter:
    def __init__(self, config_path: Optional[str] = None) -> None:
        config_path = config_path or os.environ.get("LLM_CONFIG_PATH", "llm_config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.providers: Dict[str, LLMProvider] = {}
        for provider_config in config["providers"]:
            if provider_config["name"] == "ollama":
                self.providers["ollama"] = OllamaProvider(provider_config.get("base_url"))
            # Add other providers here

        self.budget_manager = BudgetManager(config.get("budgets", {}))
        self.cache: Dict[str, Any] = {}

    def _get_provider(self, model: str) -> LLMProvider:
        # Simple logic for now: use ollama if the model is available there, otherwise error
        if "ollama" in self.providers:
            return self.providers["ollama"]
        raise ModelUnavailableError(model, "No provider available for this model")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        model_name = model or "llama3:8b"
        cache_key = f"{model_name}-{temperature}-{max_tokens}-{str(messages)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        provider = self._get_provider(model_name)

        # Dummy values for token and cost for now
        tokens = 100
        cost_usd = 0.0001

        if not self.budget_manager.check_budget(provider.name, tokens, cost_usd):
            raise ModelUnavailableError(model_name, "Budget exceeded")

        response = await provider.chat(messages, model_name, temperature, max_tokens)
        self.budget_manager.update_budget(provider.name, tokens, cost_usd)
        self.cache[cache_key] = response
        return response

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        model_name = model or "llama3:8b"
        provider = self._get_provider(model_name)

        # Dummy values for token and cost for now
        tokens = 100
        cost_usd = 0.0001

        if not self.budget_manager.check_budget(provider.name, tokens, cost_usd):
            raise ModelUnavailableError(model_name, "Budget exceeded")

        async for chunk in provider.stream_chat(messages, model_name, temperature):
            yield chunk

        self.budget_manager.update_budget(provider.name, tokens, cost_usd)