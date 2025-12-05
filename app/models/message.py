from pydantic import BaseModel
from typing import List, Optional
from .card import Card


class InitMessage(BaseModel):
    type: str = "init"
    you: str
    hand: List[Card]
    landlord_id: Optional[str]


class PlayRequest(BaseModel):
    type: str = "play"
    cards: List[Card]


class PlayResultMessage(BaseModel):
    type: str = "play_result"
    ok: bool
    error: Optional[str] = None


class BotPlayMessage(BaseModel):
    type: str = "bot_play"
    player_id: str
    cards: List[Card]


class GameOverMessage(BaseModel):
    type: str = "game_over"
    winner: str  # "landlord" / "farmers"
    landlord_id: str
