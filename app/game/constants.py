from enum import Enum
from typing import List


class PlayerRole(str, Enum):
    LANDLORD = "landlord"
    FARMER = "farmer"


PLAYER_IDS: List[str] = ["human", "bot1", "bot2"]


class CardType(str, Enum):
    SINGLE = "single"
    PAIR = "pair"
    TRIPLE = "triple"
    TRIPLE_SINGLE = "triple_single"
    TRIPLE_PAIR = "triple_pair"
    STRAIGHT = "straight"
    DOUBLE_SEQUENCE = "double_sequence"
    AIRPLANE = "airplane"  # 不带
    AIRPLANE_SINGLE = "airplane_single"
    AIRPLANE_PAIR = "airplane_pair"
    BOMB = "bomb"
    ROCKET = "rocket"  # 王炸
