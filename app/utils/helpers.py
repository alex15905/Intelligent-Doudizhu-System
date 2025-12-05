import uuid
from typing import List
from app.models.card import Card


def generate_room_id() -> str:
    """生成简单房间 ID。"""
    return uuid.uuid4().hex[:8]


def cards_to_str(cards: List[Card]) -> str:
    """将一组牌转成人类可读字符串（用于日志）。"""
    if not cards:
        return "PASS"
    rank_map = {
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "J",
        12: "Q",
        13: "K",
        14: "A",
        15: "2",
        16: "SJ",
        17: "BJ",
    }
    suit_map = {"S": "♠", "H": "♥", "D": "♦", "C": "♣", "J": ""}
    parts = []
    for c in cards:
        r = rank_map.get(c.rank, str(c.rank))
        s = suit_map.get(c.suit, "?")
        parts.append(f"{s}{r}")
    return " ".join(parts)
