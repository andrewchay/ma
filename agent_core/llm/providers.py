"""LLM Provider implementations"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        self.extra_kwargs = kwargs
    
    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable"""
        pass
    
    @abstractmethod
    def _get_default_model(self) -> str:
        """Get default model name"""
        pass
    
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Complete a prompt and return the response"""
        pass
    
    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Chat completion with message history"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider"""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")
    
    def _get_default_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        except Exception as e:
            return f"[OpenAI Error: {str(e)}]"
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        except Exception as e:
            return f"[OpenAI Error: {str(e)}]"


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider"""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")
    
    def _get_default_model(self) -> str:
        return os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                system=system_prompt or "",
                messages=messages,
            )
            return response.content[0].text
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            return f"[Claude Error: {str(e)}]"
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                if msg["role"] != "system":
                    claude_messages.append(msg)
            
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                system=system_msg,
                messages=claude_messages,
            )
            return response.content[0].text
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            return f"[Claude Error: {str(e)}]"


class KimiProvider(BaseProvider):
    """Moonshot AI (Kimi) provider - 月之暗面"""
    
    # 可用模型列表 (2024最新)
    AVAILABLE_MODELS = [
        "kimi-k2.5",             # K2.5 最新版本 (推荐)
        "kimi-k2",               # K2 版本
        "kimi-latest",           # 始终指向最新版本
        "moonshot-v1-8k",        # 标准上下文 (8k)
        "moonshot-v1-32k",       # 长上下文 (32k)
        "moonshot-v1-128k",      # 超长上下文 (128k)
        "moonshot-v1-auto",      # 自动选择上下文
    ]
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("KIMI_API_KEY")
    
    def _get_default_model(self) -> str:
        return os.getenv("KIMI_MODEL", "kimi-k2.5")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        except Exception as e:
            return f"[Kimi Error: {str(e)}]"
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        except Exception as e:
            return f"[Kimi Error: {str(e)}]"


class MinimaxProvider(BaseProvider):
    """Minimax provider"""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("MINIMAX_API_KEY")
    
    def _get_default_model(self) -> str:
        return os.getenv("MINIMAX_MODEL", "abab6.5-chat")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            import requests
            
            group_id = os.getenv("MINIMAX_GROUP_ID", "")
            url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Minimax Error: {str(e)}]"
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            import requests
            
            group_id = os.getenv("MINIMAX_GROUP_ID", "")
            url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Minimax Error: {str(e)}]"


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider (OpenAI compatible API)"""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("DEEPSEEK_API_KEY")
    
    def _get_default_model(self) -> str:
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    def _make_request(self, messages: list[dict], **kwargs) -> str:
        """Make HTTP request to DeepSeek API"""
        import urllib.request
        import urllib.error
        import json
        
        url = "https://api.deepseek.com/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"[DeepSeek Error {e.code}: {error_body}]"
        except Exception as e:
            return f"[DeepSeek Error: {str(e)}]"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return self._make_request(messages, **kwargs)
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self._make_request(messages, **kwargs)


class MockProvider(BaseProvider):
    """Mock provider for testing without API keys"""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return "mock"
    
    def _get_default_model(self) -> str:
        return "mock"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return f"[Mock LLM Response] 收到提示: {prompt[:50]}..."
    
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return f"[Mock LLM Response] 收到 {len(messages)} 条消息"
