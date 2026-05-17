"""Tests for the model provider module (src/services/agents/model_provider.py).

Tests verify:
- _ConfiguredLitellmProvider correctly identifies native vs proxy provider models
- Native providers (gemini/, anthropic/, etc.) get base_url=None
- Proxy models receive the configured base_url
- get_run_config() returns a valid RunConfig instance
"""

from unittest.mock import patch, MagicMock

import pytest

from src.services.agents.model_provider import (
    _NATIVE_PROVIDER_PREFIXES,
    _ConfiguredLitellmProvider,
    get_run_config,
)


class TestNativeProviderPrefixes:
    """Tests for the _NATIVE_PROVIDER_PREFIXES constant."""

    def test_prefixes_is_tuple(self):
        assert isinstance(_NATIVE_PROVIDER_PREFIXES, tuple)

    def test_prefixes_not_empty(self):
        assert len(_NATIVE_PROVIDER_PREFIXES) > 0

    def test_gemini_prefix_present(self):
        assert "gemini/" in _NATIVE_PROVIDER_PREFIXES

    def test_anthropic_prefix_present(self):
        assert "anthropic/" in _NATIVE_PROVIDER_PREFIXES

    def test_cohere_prefix_present(self):
        assert "cohere/" in _NATIVE_PROVIDER_PREFIXES

    def test_mistral_prefix_present(self):
        assert "mistral/" in _NATIVE_PROVIDER_PREFIXES


class TestConfiguredLitellmProvider:
    """Tests for _ConfiguredLitellmProvider.get_model()."""

    @pytest.mark.parametrize(
        "model_name",
        [
            "gemini/gemini-pro",
            "gemini/gemini-1.5-flash",
            "anthropic/claude-3-5-sonnet",
            "cohere/command",
            "ai21/j2-ultra",
            "mistral/mistral-large",
        ],
    )
    def test_native_provider_models_get_no_base_url(self, model_name):
        """Native provider models must not receive a proxy base_url."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gemini/gemini-pro"
            mock_settings.LLM_BASE_URL = "https://proxy.example.com"
            mock_settings.LLM_API_KEY = "test-key"

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model(model_name)

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["base_url"] is None, (
                    f"Native provider {model_name} should have base_url=None, "
                    f"got {call_kwargs['base_url']}"
                )

    @pytest.mark.parametrize(
        "model_name",
        [
            "openrouter/gpt-4",
            "gpt-4",
            "gpt-3.5-turbo",
            "ollama/llama3",
        ],
    )
    def test_proxy_models_receive_base_url(self, model_name):
        """Non-native (proxy) models should receive the configured base_url."""
        provider = _ConfiguredLitellmProvider()
        configured_base_url = "https://proxy.example.com"

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = model_name
            mock_settings.LLM_BASE_URL = configured_base_url
            mock_settings.LLM_API_KEY = "test-key"

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model(model_name)

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["base_url"] == configured_base_url

    def test_model_name_none_falls_back_to_settings(self):
        """When model_name is None, should use settings.LLM_MODEL."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gemini/gemini-pro"
            mock_settings.LLM_BASE_URL = "https://proxy.example.com"
            mock_settings.LLM_API_KEY = "test-key"

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model(None)

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["model"] == "gemini/gemini-pro"

    def test_api_key_passed_to_model(self):
        """LLM_API_KEY should be forwarded to LitellmModel."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.LLM_BASE_URL = ""
            mock_settings.LLM_API_KEY = "sk-super-secret"

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model("gpt-4")

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["api_key"] == "sk-super-secret"

    def test_empty_api_key_becomes_none(self):
        """An empty string LLM_API_KEY should resolve to None."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.LLM_BASE_URL = ""
            mock_settings.LLM_API_KEY = ""

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model("gpt-4")

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["api_key"] is None

    def test_empty_base_url_becomes_none_for_proxy_model(self):
        """Empty LLM_BASE_URL should resolve to None even for proxy models."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.LLM_BASE_URL = ""
            mock_settings.LLM_API_KEY = "key"

            with patch("src.services.agents.model_provider.LitellmModel") as mock_model_cls:
                mock_model_cls.return_value = MagicMock()
                provider.get_model("gpt-4")

                call_kwargs = mock_model_cls.call_args[1]
                assert call_kwargs["base_url"] is None

    def test_model_returned(self):
        """get_model should return the result of LitellmModel()."""
        provider = _ConfiguredLitellmProvider()

        with patch("src.services.agents.model_provider.settings") as mock_settings:
            mock_settings.LLM_MODEL = "gemini/pro"
            mock_settings.LLM_BASE_URL = None
            mock_settings.LLM_API_KEY = "key"

            mock_model_instance = MagicMock()
            with patch(
                "src.services.agents.model_provider.LitellmModel",
                return_value=mock_model_instance,
            ):
                result = provider.get_model("gemini/gemini-pro")
                assert result is mock_model_instance

    def test_provider_is_model_provider_subclass(self):
        """_ConfiguredLitellmProvider must be a subclass of ModelProvider."""
        from agents.models.interface import ModelProvider
        assert issubclass(_ConfiguredLitellmProvider, ModelProvider)


class TestGetRunConfig:
    """Tests for get_run_config()."""

    def test_returns_run_config(self):
        """get_run_config should return a RunConfig object."""
        from agents import RunConfig
        config = get_run_config()
        assert isinstance(config, RunConfig)

    def test_run_config_has_model_provider(self):
        """The returned RunConfig must have a model_provider set."""
        config = get_run_config()
        assert config.model_provider is not None

    def test_run_config_provider_is_configured_litellm(self):
        """The model_provider must be an instance of _ConfiguredLitellmProvider."""
        config = get_run_config()
        assert isinstance(config.model_provider, _ConfiguredLitellmProvider)

    def test_each_call_returns_new_instance(self):
        """Each call to get_run_config should return a new RunConfig."""
        config1 = get_run_config()
        config2 = get_run_config()
        assert config1 is not config2