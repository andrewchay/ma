"""LLM Client for MA Agent"""
from __future__ import annotations

import json
import os
from typing import Any, Optional, Union

from agent_core.llm.providers import (
    BaseProvider,
    OpenAIProvider,
    ClaudeProvider,
    KimiProvider,
    MinimaxProvider,
    DeepSeekProvider,
    MockProvider,
)


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "kimi": KimiProvider,
        "minimax": MinimaxProvider,
        "deepseek": DeepSeekProvider,
        "mock": MockProvider,
    }
    
    def __init__(self, provider: Optional[str] = None, **kwargs):
        """
        Initialize LLM client
        
        Args:
            provider: Provider name (openai/claude/kimi/minimax/mock)
            **kwargs: Additional arguments passed to provider
        """
        provider = provider or os.getenv("LLM_PROVIDER", "mock")
        provider_class = self.PROVIDERS.get(provider.lower(), MockProvider)
        self.provider: BaseProvider = provider_class(**kwargs)
        self.provider_name = provider.lower()
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        **kwargs
    ) -> Union[str, dict]:
        """
        Complete a prompt
        
        Args:
            prompt: The prompt to complete
            system_prompt: Optional system prompt
            json_mode: If True, parse response as JSON
            **kwargs: Additional provider-specific arguments
        
        Returns:
            Response string or parsed JSON if json_mode=True
        """
        if json_mode and self.provider_name == "openai":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.provider.complete(prompt, system_prompt, **kwargs)
        
        if json_mode:
            try:
                # Try to extract JSON from markdown code blocks
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                else:
                    json_str = response
                return json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError) as e:
                return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": response}
        
        return response
    
    def chat(
        self,
        messages: list[dict[str, str]],
        json_mode: bool = False,
        **kwargs
    ) -> Union[str, dict]:
        """
        Chat completion with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            json_mode: If True, parse response as JSON
            **kwargs: Additional provider-specific arguments
        
        Returns:
            Response string or parsed JSON if json_mode=True
        """
        if json_mode and self.provider_name == "openai":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.provider.chat(messages, **kwargs)
        
        if json_mode:
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                else:
                    json_str = response
                return json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError) as e:
                return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": response}
        
        return response
    
    def is_available(self) -> bool:
        """Check if the provider is properly configured"""
        return self.provider.api_key is not None


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client(provider: Optional[str] = None, **kwargs) -> LLMClient:
    """Get or create global LLM client instance"""
    global _llm_client
    if _llm_client is None or provider is not None:
        _llm_client = LLMClient(provider=provider, **kwargs)
    return _llm_client


def reset_llm_client():
    """Reset global LLM client (for testing)"""
    global _llm_client
    _llm_client = None
