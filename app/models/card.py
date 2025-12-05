# -*- coding: utf-8 -*-
"""
扑克牌与观测数据结构（不再依赖 pydantic）
"""

from typing import List, Optional


class Card:
    """
    扑克牌：
    rank:
        3-14: 3-10, J=11, Q=12, K=13, A=14
        15:   2
        16:   小王
        17:   大王
    suit:
        'S','H','D','C' 普通花色
        'J'              王
    """

    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str):
        self.rank = int(rank)
        self.suit = str(suit)

    def __lt__(self, other: "Card") -> bool:
        """排序用"""
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.suit < other.suit

    def dict(self) -> dict:
        """兼容原来 pydantic.BaseModel 的 .dict() 用法"""
        return {"rank": self.rank, "suit": self.suit}

    def __repr__(self) -> str:
        return f"Card(rank={self.rank}, suit={self.suit})"


class ActionRecord:
    """
    行为记录：出牌 / PASS / 叫分 等
    """

    __slots__ = ("player_id", "cards", "action_type")

    def __init__(self, player_id: str, cards: List[Card], action_type: str):
        self.player_id = player_id
        self.cards = list(cards) if cards is not None else []
        self.action_type = action_type

    def __repr__(self) -> str:
        return f"ActionRecord(player_id={self.player_id}, cards={self.cards}, action_type={self.action_type})"


class Observation:
    """
    AI / 前端看到的局面视图。
    这以前是 pydantic.BaseModel，现在用普通类实现，字段保持不变。
    """

    __slots__ = (
        "my_id",
        "my_hand",
        "public_history",
        "landlord_id",
        "current_turn",
        "last_play",
        "last_non_pass",
    )

    def __init__(
        self,
        my_id: str,
        my_hand: List[Card],
        public_history: List[ActionRecord],
        landlord_id: Optional[str],
        current_turn: str,
        last_play: Optional[ActionRecord] = None,
        last_non_pass: Optional[ActionRecord] = None,
    ):
        self.my_id = my_id
        self.my_hand = list(my_hand) if my_hand is not None else []
        self.public_history = list(public_history) if public_history is not None else []
        self.landlord_id = landlord_id
        self.current_turn = current_turn
        self.last_play = last_play
        self.last_non_pass = last_non_pass

    def __repr__(self) -> str:
        return (
            f"Observation(my_id={self.my_id}, "
            f"hand={self.my_hand}, "
            f"landlord_id={self.landlord_id}, "
            f"current_turn={self.current_turn}, "
            f"last_play={self.last_play}, "
            f"last_non_pass={self.last_non_pass})"
        )
