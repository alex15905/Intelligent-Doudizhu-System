from abc import ABC, abstractmethod
from typing import List
from app.models.card import Card, Observation


class AIEngineBase(ABC):
    """
    AI 引擎基类：只知道 Observation，不知道完整发牌信息。
    """

    def __init__(self, device: str = "cpu") -> None:
        self.device = device

    @abstractmethod
    def choose_action(self, obs: Observation) -> List[Card]:
        """
        根据观察到的局面，返回要出的牌（可以为空列表 => PASS）。
        """
        raise NotImplementedError
