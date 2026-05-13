"""Shared LiteLLM model provider and RunConfig factory.

Centralised here so both the API layer and internal guardrail runners
can obtain a consistent RunConfig without duplicating the provider class.
"""

from agents import RunConfig
from agents.extensions.models.litellm_model import LitellmModel
from agents.models.interface import Model, ModelProvider

from src.config import settings



_NATIVE_PROVIDER_PREFIXES = ("gemini/", "anthropic/", "cohere/", "ai21/", "mistral/")


class _ConfiguredLitellmProvider(ModelProvider):
    """LitellmProvider wired to project LLM settings."""

    def get_model(self, model_name: str | None) -> Model:
        model = model_name or settings.LLM_MODEL
        # Native provider models (gemini/, anthropic/, etc.) have their own API
        # endpoints and must not receive a proxy base_url — only OpenAI-compatible
        # proxy models (e.g. openrouter/...) should use the configured base_url.
        is_native = any(model.startswith(p) for p in _NATIVE_PROVIDER_PREFIXES)
        return LitellmModel(
            model=model,
            base_url=None if is_native else (settings.LLM_BASE_URL or None),
            api_key=settings.LLM_API_KEY or None,
        )


def get_run_config() -> RunConfig:
    """Return a RunConfig using the project-configured LiteLLM provider."""
    return RunConfig(model_provider=_ConfiguredLitellmProvider())
