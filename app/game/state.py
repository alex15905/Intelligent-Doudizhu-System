# -*- coding: utf-8 -*-
"""
游戏整体状态数据结构（不再依赖 pydantic）
"""

from typing import Dict, List, Optional
from app.models.card import Card, ActionRecord
from app.game.constants import PlayerRole, PLAYER_IDS


class PlayerState:
    """
    单个玩家状态
    """

    __slots__ = ("player_id", "role", "hand")

    def __init__(self, player_id: str, role: PlayerRole, hand: Optional[List[Card]] = None):
        self.player_id = player_id
        self.role = role
        self.hand = list(hand) if hand is not None else []

    def __repr__(self) -> str:
        return f"PlayerState(player_id={self.player_id}, role={self.role}, hand_len={len(self.hand)})"


class GameState:
    """
    整个局面的状态，原来是 pydantic.BaseModel，现在改为普通类。
    字段布局保持完全一致，供 DealerReferee 使用。
    """

    __slots__ = (
        "players",
        "bottom_cards",
        "landlord_id",
        "current_turn",
        "history",
        "last_play",
        "last_non_pass",
        "multiplier",
        "game_over",
        "winner_side",
    )

    def __init__(
        self,
        players: Dict[str, PlayerState],
        bottom_cards: List[Card],
        landlord_id: Optional[str],
        current_turn: str,
        history: List[ActionRecord],
        last_play: Optional[ActionRecord],
        last_non_pass: Optional[ActionRecord],
        multiplier: int,
        game_over: bool,
        winner_side: Optional[str],
    ):
        self.players = players
        self.bottom_cards = list(bottom_cards) if bottom_cards is not None else []
        self.landlord_id = landlord_id
        self.current_turn = current_turn
        self.history = list(history) if history is not None else []
        self.last_play = last_play
        self.last_non_pass = last_non_pass
        self.multiplier = multiplier
        self.game_over = game_over
        self.winner_side = winner_side

    @classmethod
    def initial(cls) -> "GameState":
        """
        创建一局初始空状态。
        """
        players: Dict[str, PlayerState] = {
            pid: PlayerState(player_id=pid, role=PlayerRole.FARMER, hand=[])
            for pid in PLAYER_IDS
        }
        return cls(
            players=players,
            bottom_cards=[],
            landlord_id=None,
            current_turn="human",
            history=[],
            last_play=None,
            last_non_pass=None,
            multiplier=1,
            game_over=False,
            winner_side=None,
        )

    def hands_left(self) -> Dict[str, int]:
        """
        返回每个玩家剩余手牌数量。
        """
        return {pid: len(ps.hand) for pid, ps in self.players.items()}

    def __repr__(self) -> str:
        return (
            f"GameState(landlord_id={self.landlord_id}, "
            f"current_turn={self.current_turn}, "
            f"multiplier={self.multiplier}, "
            f"game_over={self.game_over}, "
            f"winner_side={self.winner_side})"
        )
