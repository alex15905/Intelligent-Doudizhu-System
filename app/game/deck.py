from typing import List
from secrets import SystemRandom
from app.models.card import Card


_rng = SystemRandom()


def new_deck() -> List[Card]:
    """
    生成完整一副牌 54 张：
      3-A,2 共 13 点 *4
      小王、大王
    rank 映射：
      3-14: 3-10, J,Q,K,A
      15:   2
      16:   小王
      17:   大王
    """
    deck: List[Card] = []
    ranks = list(range(3, 15)) + [15]  # 3-14, 15=2
    suits = ["S", "H", "D", "C"]
    for r in ranks:
        for s in suits:
            deck.append(Card(rank=r, suit=s))

    # 小王、大王
    deck.append(Card(rank=16, suit="J"))
    deck.append(Card(rank=17, suit="J"))
    return deck


def shuffle_deck(deck: List[Card]) -> None:
    """原地洗牌。"""
    _rng.shuffle(deck)
