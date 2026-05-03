"""
LLM 客户端模块

统一的 LLM 调用接口，支持 Anthropic Claude / OpenAI GPT / Mock
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端基类"""

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed: pip install anthropic")
                raise
        return self._client

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


class OpenAIClient(LLMClient):
    """OpenAI GPT 客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("openai package not installed: pip install openai")
                raise
        return self._client

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端 - 用于测试或无 AI 环境"""

    def generate(self, prompt: str, **kwargs) -> str:
        logger.warning("Using mock LLM client, returning empty response")
        return json.dumps(
            {"name": "mock_strategy", "description": "Mock strategy", "conditions": []}
        )


def create_llm_client(
    provider: str, api_key: str, model: Optional[str] = None
) -> LLMClient:
    """
    LLM 客户端工厂函数

    Args:
        provider: 提供商名称 (anthropic / openai / mock)
        api_key: API 密钥
        model: 模型名称

    Returns:
        对应的 LLMClient 实例
    """
    clients = {
        "anthropic": lambda: AnthropicClient(api_key, model or "claude-sonnet-4-6"),
        "openai": lambda: OpenAIClient(api_key, model or "gpt-4"),
        "mock": lambda: MockLLMClient(),
    }

    factory = clients.get(provider)
    if factory is None:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return factory()
