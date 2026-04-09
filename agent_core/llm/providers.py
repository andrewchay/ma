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

    def _build_candidate_urls(self) -> list[str]:
        """
        Build candidate endpoint URLs.

        Supports both historical and newer domains, and optional GroupId.
        """
        group_id = os.getenv("MINIMAX_GROUP_ID", "").strip()
        custom_base = os.getenv("MINIMAX_BASE_URL", "").strip()

        bases = []
        if custom_base:
            bases.append(custom_base.rstrip("/"))
        bases.extend(
            [
                "https://api.minimax.chat/v1/text/chatcompletion_v2",
                "https://api.minimax.io/v1/text/chatcompletion_v2",
            ]
        )

        urls: list[str] = []
        for base in bases:
            if "{group_id}" in base:
                urls.append(base.replace("{group_id}", group_id))
            elif group_id and "GroupId=" not in base:
                sep = "&" if "?" in base else "?"
                urls.append(f"{base}{sep}GroupId={group_id}")
            else:
                urls.append(base)
        return urls

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        """Extract content from different Minimax response shapes."""
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if isinstance(p, dict)]
                if any(text_parts):
                    return "\n".join([p for p in text_parts if p])

        for key in ("reply", "output_text", "text"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value

        base_resp = data.get("base_resp", {})
        if isinstance(base_resp, dict):
            status_msg = base_resp.get("status_msg")
            if isinstance(status_msg, str) and status_msg:
                return f"[Minimax Error: {status_msg}]"

        return f"[Minimax Error: unexpected response schema: {data}]"

    def _post_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            import requests
        except ImportError:
            raise ImportError("requests package not installed. Run: pip install requests")

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

        timeout = kwargs.get("timeout", 60)
        last_error: Optional[str] = None
        for url in self._build_candidate_urls():
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                return self._extract_text(response.json())
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                # Fast-fail auth/permission errors.
                if status in (401, 403):
                    body = e.response.text if e.response is not None else str(e)
                    return f"[Minimax Error {status}: {body}]"
                body = e.response.text if e.response is not None else str(e)
                last_error = f"HTTP {status}: {body}"
            except Exception as e:
                last_error = str(e)

        return f"[Minimax Error: request failed on all endpoints: {last_error}]"

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self._post_chat(messages, **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self._post_chat(messages, **kwargs)


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
