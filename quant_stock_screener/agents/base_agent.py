"""
基础 Agent 类

所有 AI Agent 的基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    AI Agent 基类

    所有智能代理都继承此类，提供统一的接口和基础功能
    """

    def __init__(self, agent_name: str, llm_client=None):
        """
        初始化 Agent

        Args:
            agent_name: Agent 名称
            llm_client: LLM 客户端实例
        """
        self.agent_name = agent_name
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"agent.{agent_name}")

    @property
    def is_available(self) -> bool:
        """检查 Agent 是否可用（需要 LLM 客户端）"""
        return self.llm_client is not None

    def set_llm_client(self, llm_client):
        """设置 LLM 客户端"""
        self.llm_client = llm_client

    def _generate_response(self, prompt: str, **kwargs) -> Optional[str]:
        """
        调用 LLM 生成响应

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            LLM 响应文本，失败返回 None
        """
        if not self.is_available:
            self.logger.warning(f"Agent {self.agent_name} 不可用：未配置 LLM 客户端")
            return None

        try:
            response = self.llm_client.generate(prompt, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"Agent {self.agent_name} 生成响应失败: {e}")
            return None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行 Agent 任务

        Args:
            **kwargs: 任务参数

        Returns:
            任务结果
        """
        pass

    def get_status(self) -> Dict:
        """获取 Agent 状态信息"""
        return {
            "name": self.agent_name,
            "available": self.is_available,
            "type": self.__class__.__name__,
        }
