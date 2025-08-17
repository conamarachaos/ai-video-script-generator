"""Factory for creating LLM instances based on provider configuration."""

from typing import Optional, Dict
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
# DeepSeek uses OpenAI-compatible API

from .config import ModelProvider, ModelConfig, Settings


class ModelFactory:
    """Factory class for creating LLM instances."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the model factory with settings."""
        self.settings = settings or Settings()
        self._validate_api_keys()
    
    def _validate_api_keys(self):
        """Validate that required API keys are present."""
        providers_keys = {
            ModelProvider.CLAUDE: self.settings.anthropic_api_key,
            ModelProvider.OPENAI: self.settings.openai_api_key,
            ModelProvider.DEEPSEEK: self.settings.deepseek_api_key,
            ModelProvider.GEMINI: self.settings.google_api_key
        }
        
        self.available_providers = {
            provider: key is not None 
            for provider, key in providers_keys.items()
        }
    
    def create_model(self, config: ModelConfig) -> BaseChatModel:
        """
        Create an LLM instance based on the configuration.
        
        Args:
            config: Model configuration specifying provider and parameters
            
        Returns:
            Initialized LLM instance
            
        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        if not self.available_providers.get(config.provider):
            raise ValueError(
                f"API key for {config.provider} is not configured. "
                f"Please set the corresponding environment variable."
            )
        
        provider_map = {
            ModelProvider.CLAUDE: self._create_claude,
            ModelProvider.OPENAI: self._create_openai,
            ModelProvider.DEEPSEEK: self._create_deepseek,
            ModelProvider.GEMINI: self._create_gemini
        }
        
        creator = provider_map.get(config.provider)
        if not creator:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        return creator(config)
    
    def _create_claude(self, config: ModelConfig) -> ChatAnthropic:
        """Create a Claude model instance."""
        kwargs = {
            "model_name": config.model,  # ChatAnthropicMessages uses model_name
            "anthropic_api_key": self.settings.anthropic_api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": self.settings.request_timeout,
            "max_retries": self.settings.max_retries
        }
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        
        # Add any custom headers (e.g., for 1M context)
        if config.headers:
            kwargs["default_headers"] = config.headers
        
        return ChatAnthropic(**kwargs)
    
    def _create_openai(self, config: ModelConfig) -> ChatOpenAI:
        """Create an OpenAI model instance."""
        kwargs = {
            "model": config.model,
            "openai_api_key": self.settings.openai_api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": self.settings.request_timeout,
            "max_retries": self.settings.max_retries
        }
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.frequency_penalty is not None:
            kwargs["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty is not None:
            kwargs["presence_penalty"] = config.presence_penalty
        
        return ChatOpenAI(**kwargs)
    
    def _create_deepseek(self, config: ModelConfig) -> ChatOpenAI:
        """Create a DeepSeek model instance using OpenAI-compatible API."""
        kwargs = {
            "model": config.model,
            "api_key": self.settings.deepseek_api_key,
            "base_url": "https://api.deepseek.com/v1",
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": self.settings.request_timeout,
            "max_retries": self.settings.max_retries
        }
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.frequency_penalty is not None:
            kwargs["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty is not None:
            kwargs["presence_penalty"] = config.presence_penalty
        
        return ChatOpenAI(**kwargs)  # DeepSeek uses OpenAI client
    
    def _create_gemini(self, config: ModelConfig) -> ChatGoogleGenerativeAI:
        """Create a Gemini model instance."""
        # Set environment to reduce warnings
        import os
        os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
        
        kwargs = {
            "model": config.model,
            "google_api_key": self.settings.google_api_key,
            "temperature": config.temperature,
            "max_output_tokens": config.max_tokens,
            "timeout": self.settings.request_timeout,
            "max_retries": self.settings.max_retries,
            "convert_system_message_to_human": True  # Avoid warnings about system messages
        }
        
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        
        return ChatGoogleGenerativeAI(**kwargs)
    
    def get_available_providers(self) -> Dict[ModelProvider, bool]:
        """Get dictionary of available providers based on configured API keys."""
        return self.available_providers
    
    def create_fallback_chain(self, primary_config: ModelConfig, 
                            fallback_configs: list[ModelConfig]) -> BaseChatModel:
        """
        Create a model with fallback options.
        
        Args:
            primary_config: Primary model configuration
            fallback_configs: List of fallback configurations
            
        Returns:
            Model instance with fallback chain
        """
        primary = self.create_model(primary_config)
        fallbacks = [self.create_model(config) for config in fallback_configs]
        
        return primary.with_fallbacks(fallbacks)


# Singleton instance
_factory_instance: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """Get or create the singleton ModelFactory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ModelFactory()
    return _factory_instance


def create_model_for_agent(agent_role: str) -> BaseChatModel:
    """
    Convenience function to create a model for a specific agent role.
    
    Args:
        agent_role: The role of the agent
        
    Returns:
        Configured LLM instance
    """
    from .config import DEFAULT_AGENT_CONFIGS, AgentRole
    
    factory = get_model_factory()
    agent_config = DEFAULT_AGENT_CONFIGS.get(AgentRole(agent_role))
    
    if not agent_config:
        raise ValueError(f"No default configuration for agent role: {agent_role}")
    
    return factory.create_model(agent_config.model_config)