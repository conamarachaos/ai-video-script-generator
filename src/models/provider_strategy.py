"""Provider selection strategy for optimizing LLM choice per agent role."""

from typing import Dict, Optional, Tuple
from .config import ModelProvider, AgentRole


class ProviderStrategy:
    """
    Selects the best LLM provider for each agent based on task requirements.
    
    Selection criteria:
    - Creative tasks: High temperature, creative models (Gemini Pro, GPT-4, Claude Opus)
    - Analytical tasks: Low temperature, logical models (Claude Haiku, GPT-3.5)
    - Long content: Models with high token limits (Gemini, Claude)
    - Fast response: Low-latency models (Gemini Flash, Claude Haiku, DeepSeek)
    """
    
    # Provider strengths and characteristics
    PROVIDER_PROFILES = {
        ModelProvider.GEMINI: {
            "strengths": ["creative", "long_context", "multimodal", "fast"],
            "models": {
                "gemini-1.5-pro": {"type": "creative", "max_tokens": 8192, "cost": "medium"},
                "gemini-1.5-flash": {"type": "fast", "max_tokens": 8192, "cost": "low"},
                "gemini-1.5-flash-8b": {"type": "ultra_fast", "max_tokens": 8192, "cost": "very_low"}
            }
        },
        ModelProvider.CLAUDE: {
            "strengths": ["analytical", "nuanced", "long_context", "safe"],
            "models": {
                "claude-3-opus-20240229": {"type": "creative", "max_tokens": 4096, "cost": "high"},
                "claude-3-5-sonnet-20240620": {"type": "balanced", "max_tokens": 8192, "cost": "medium"},
                "claude-3-haiku-20240307": {"type": "fast", "max_tokens": 4096, "cost": "low"}
            }
        },
        ModelProvider.OPENAI: {
            "strengths": ["general", "reliable", "structured", "code"],
            "models": {
                "gpt-4": {"type": "creative", "max_tokens": 8192, "cost": "high"},
                "gpt-4-turbo": {"type": "balanced", "max_tokens": 128000, "cost": "medium"},
                "gpt-3.5-turbo": {"type": "fast", "max_tokens": 4096, "cost": "low"}
            }
        },
        ModelProvider.DEEPSEEK: {
            "strengths": ["cost_effective", "fast", "general"],
            "models": {
                "deepseek-chat": {"type": "balanced", "max_tokens": 4096, "cost": "very_low"}
            }
        }
    }
    
    # Agent role requirements
    AGENT_REQUIREMENTS = {
        AgentRole.ORCHESTRATOR: {
            "needs": ["analytical", "fast", "reliable"],
            "temperature": 0.3,
            "preferred_providers": [ModelProvider.CLAUDE, ModelProvider.GEMINI, ModelProvider.OPENAI],
            "preferred_models": {
                ModelProvider.CLAUDE: "claude-3-haiku-20240307",
                ModelProvider.GEMINI: "gemini-1.5-flash",
                ModelProvider.OPENAI: "gpt-3.5-turbo",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.HOOK_SPECIALIST: {
            "needs": ["creative", "viral_understanding", "emotional"],
            "temperature": 0.8,
            "preferred_providers": [ModelProvider.GEMINI, ModelProvider.OPENAI, ModelProvider.CLAUDE],
            "preferred_models": {
                ModelProvider.GEMINI: "gemini-1.5-pro",
                ModelProvider.CLAUDE: "claude-3-opus-20240229",
                ModelProvider.OPENAI: "gpt-4",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.STORY_ARCHITECT: {
            "needs": ["creative", "structured", "long_context"],
            "temperature": 0.7,
            "preferred_providers": [ModelProvider.GEMINI, ModelProvider.CLAUDE, ModelProvider.OPENAI],
            "preferred_models": {
                ModelProvider.CLAUDE: "claude-3-haiku-20240307",
                ModelProvider.GEMINI: "gemini-1.5-pro",
                ModelProvider.OPENAI: "gpt-4-turbo",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.CTA_STRATEGIST: {
            "needs": ["persuasive", "analytical", "conversion_focused"],
            "temperature": 0.6,
            "preferred_providers": [ModelProvider.OPENAI, ModelProvider.CLAUDE, ModelProvider.GEMINI],
            "preferred_models": {
                ModelProvider.OPENAI: "gpt-4",
                ModelProvider.CLAUDE: "claude-3-5-sonnet-20240620",
                ModelProvider.GEMINI: "gemini-1.5-pro",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.RESEARCH_ANALYST: {
            "needs": ["factual", "analytical", "thorough"],
            "temperature": 0.2,
            "preferred_providers": [ModelProvider.CLAUDE, ModelProvider.OPENAI, ModelProvider.GEMINI],
            "preferred_models": {
                ModelProvider.CLAUDE: "claude-3-haiku-20240307",
                ModelProvider.OPENAI: "gpt-3.5-turbo",
                ModelProvider.GEMINI: "gemini-1.5-flash",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.STYLIST: {
            "needs": ["creative", "nuanced", "style_matching"],
            "temperature": 0.7,
            "preferred_providers": [ModelProvider.CLAUDE, ModelProvider.GEMINI, ModelProvider.OPENAI],
            "preferred_models": {
                ModelProvider.CLAUDE: "claude-3-opus-20240229",
                ModelProvider.GEMINI: "gemini-1.5-pro",
                ModelProvider.OPENAI: "gpt-4",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        },
        AgentRole.CHALLENGER: {
            "needs": ["critical", "analytical", "thorough"],
            "temperature": 0.4,
            "preferred_providers": [ModelProvider.CLAUDE, ModelProvider.OPENAI, ModelProvider.GEMINI],
            "preferred_models": {
                ModelProvider.CLAUDE: "claude-3-5-sonnet-20240620",
                ModelProvider.OPENAI: "gpt-4",
                ModelProvider.GEMINI: "gemini-1.5-pro",
                ModelProvider.DEEPSEEK: "deepseek-chat"
            }
        }
    }
    
    def __init__(self, available_providers: Dict[ModelProvider, bool]):
        """
        Initialize with available providers.
        
        Args:
            available_providers: Dict of provider -> availability status
        """
        self.available_providers = available_providers
    
    def get_best_provider_for_agent(self, role: AgentRole) -> Tuple[Optional[ModelProvider], Optional[str], float]:
        """
        Get the best available provider and model for a specific agent role.
        
        Args:
            role: The agent role to get provider for
            
        Returns:
            Tuple of (provider, model_name, temperature) or (None, None, 0.5) if none available
        """
        agent_reqs = self.AGENT_REQUIREMENTS.get(role)
        if not agent_reqs:
            # Default fallback
            return self._get_any_available_provider()
        
        # Try preferred providers in order
        for provider in agent_reqs["preferred_providers"]:
            if self.available_providers.get(provider):
                model = agent_reqs["preferred_models"].get(provider)
                if model:
                    # Try to verify if specific model works
                    # For now, we'll assume if provider is available, preferred model works
                    return provider, model, agent_reqs["temperature"]
        
        # Fallback to any available provider
        for provider, is_available in self.available_providers.items():
            if is_available:
                model = agent_reqs["preferred_models"].get(provider)
                if model:
                    return provider, model, agent_reqs["temperature"]
        
        return None, None, 0.5
    
    def _get_any_available_provider(self) -> Tuple[Optional[ModelProvider], Optional[str], float]:
        """Get any available provider as fallback."""
        priority = [
            (ModelProvider.GEMINI, "gemini-1.5-flash"),
            (ModelProvider.CLAUDE, "claude-3-haiku-20240307"),
            (ModelProvider.OPENAI, "gpt-3.5-turbo"),
            (ModelProvider.DEEPSEEK, "deepseek-chat")
        ]
        
        for provider, model in priority:
            if self.available_providers.get(provider):
                return provider, model, 0.5
        
        return None, None, 0.5
    
    def get_provider_summary(self) -> str:
        """Get a summary of provider assignments."""
        summary = []
        for role in AgentRole:
            provider, model, temp = self.get_best_provider_for_agent(role)
            if provider and model:
                summary.append(f"{role.value}: {provider.value}/{model} (temp={temp})")
            else:
                summary.append(f"{role.value}: No provider available")
        return "\n".join(summary)
    
    def get_optimal_distribution(self) -> Dict[AgentRole, Dict]:
        """
        Get the optimal distribution of providers across all agents.
        
        Returns:
            Dict mapping agent roles to their optimal provider configuration
        """
        distribution = {}
        
        for role in AgentRole:
            provider, model, temperature = self.get_best_provider_for_agent(role)
            if provider and model:
                distribution[role] = {
                    "provider": provider,
                    "model": model,
                    "temperature": temperature,
                    "reason": self._get_selection_reason(role, provider)
                }
        
        return distribution
    
    def _get_selection_reason(self, role: AgentRole, provider: ModelProvider) -> str:
        """Get the reason for selecting a provider for an agent."""
        agent_needs = self.AGENT_REQUIREMENTS[role]["needs"]
        provider_strengths = self.PROVIDER_PROFILES[provider]["strengths"]
        
        matching_strengths = set(agent_needs) & set(provider_strengths)
        
        if matching_strengths:
            return f"Matches needs: {', '.join(matching_strengths)}"
        else:
            return "Best available option"