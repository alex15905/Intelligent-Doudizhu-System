from collections import Counter
from typing import List, Optional, Tuple, Dict
from app.models.card import Card
from app.game.constants import CardType


class ClassifiedType:
    """
    牌型识别结果：
    type: CardType
    main_rank: 用于比较大小的基准点数
    length: 用于顺子/连对/飞机的组合长度（例如顺子有几张）
    extra: 预留，当前用不到可为空
    """

    def __init__(self, type_: CardType, main_rank: int, length: int = 1, extra=None):
        self.type = type_
        self.main_rank = main_rank
        self.length = length
        self.extra = extra

    def __repr__(self) -> str:
        return f"ClassifiedType(type={self.type}, main_rank={self.main_rank}, length={self.length})"


class DouDiZhuRules:
    """
    实现斗地主牌型识别和比较：
      - 允许：三带一 / 三带二
      - 禁止：四带二（任意形式的四带牌都不合法）
      - 炸弹 = 纯四张相同牌，不能带牌
      - 王炸：小王+大王
    """

    @staticmethod
    def _rank_counts(cards: List[Card]) -> Dict[int, int]:
        return Counter([c.rank for c in cards])

    @staticmethod
    def _is_rocket(cards: List[Card]) -> Optional[ClassifiedType]:
        if len(cards) == 2:
            ranks = sorted([c.rank for c in cards])
            if set(ranks) == {16, 17}:
                return ClassifiedType(CardType.ROCKET, main_rank=17)
        return None

    @staticmethod
    def _is_bomb(cards: List[Card]) -> Optional[ClassifiedType]:
        if len(cards) == 4:
            counts = DouDiZhuRules._rank_counts(cards)
            if len(counts) == 1:
                r = next(iter(counts.keys()))
                return ClassifiedType(CardType.BOMB, main_rank=r)
        return None

    @staticmethod
    def _is_single(cards: List[Card]) -> Optional[ClassifiedType]:
        if len(cards) == 1:
            return ClassifiedType(CardType.SINGLE, main_rank=cards[0].rank)
        return None

    @staticmethod
    def _is_pair(cards: List[Card]) -> Optional[ClassifiedType]:
        if len(cards) == 2:
            counts = DouDiZhuRules._rank_counts(cards)
            if len(counts) == 1:
                r = next(iter(counts.keys()))
                return ClassifiedType(CardType.PAIR, main_rank=r)
        return None

    @staticmethod
    def _is_triple_or_with(cards: List[Card]) -> Optional[ClassifiedType]:
        """
        三张 / 三带一 / 三带二
        """
        n = len(cards)
        counts = DouDiZhuRules._rank_counts(cards)
        if 3 not in counts.values() or len(cards) < 3:
            return None

        triple_rank = None
        for r, cnt in counts.items():
            if cnt == 3:
                triple_rank = r
                break
        if triple_rank is None:
            return None

        if n == 3:
            return ClassifiedType(CardType.TRIPLE, main_rank=triple_rank)
        elif n == 4:
            # 三带一
            return ClassifiedType(CardType.TRIPLE_SINGLE, main_rank=triple_rank)
        elif n == 5:
            # 三带二：需要出现一个 3 和一个 2 的组合
            if sorted(counts.values()) == [2, 3]:
                return ClassifiedType(CardType.TRIPLE_PAIR, main_rank=triple_rank)
        return None

    @staticmethod
    def _is_straight(cards: List[Card]) -> Optional[ClassifiedType]:
        """
        顺子：>=5，连续，不含 2/王
        """
        n = len(cards)
        if n < 5:
            return None
        ranks = sorted({c.rank for c in cards})
        if len(ranks) != n:
            return None
        # 不含 2/王
        if any(r >= 15 for r in ranks):  # 15 是 2
            return None
        for i in range(len(ranks) - 1):
            if ranks[i + 1] != ranks[i] + 1:
                return None
        return ClassifiedType(CardType.STRAIGHT, main_rank=ranks[-1], length=n)

    @staticmethod
    def _is_double_sequence(cards: List[Card]) -> Optional[ClassifiedType]:
        """
        连对：>=3 对，连续，不含 2/王
        """
        n = len(cards)
        if n < 6 or n % 2 != 0:
            return None
        counts = DouDiZhuRules._rank_counts(cards)
        if any(cnt != 2 for cnt in counts.values()):
            return None
        ranks = sorted(counts.keys())
        if any(r >= 15 for r in ranks):
            return None
        for i in range(len(ranks) - 1):
            if ranks[i + 1] != ranks[i] + 1:
                return None
        return ClassifiedType(
            CardType.DOUBLE_SEQUENCE,
            main_rank=ranks[-1],
            length=len(ranks),
        )

    @staticmethod
    def _is_airplane_and_wings(cards: List[Card]) -> Optional[ClassifiedType]:
        """
        飞机及带翅膀：
          - 至少两组三张，连续，不含 2/王
          - 可以不带
          - 或 带同数量的单牌
          - 或 带同数量的对子
        """
        n = len(cards)
        counts = DouDiZhuRules._rank_counts(cards)

        triples = [r for r, c in counts.items() if c >= 3]
        if len(triples) < 2:
            return None

        # 把三张部分抽出来试
        triples_sorted = sorted(triples)
        # 不含 2/王
        if any(r >= 15 for r in triples_sorted):
            return None

        # 找最长连续三顺
        triples_sorted = sorted(triples_sorted)
        # 这里要求所有三张必须构成一个连续段，否则不判飞机（简化实现）
        for i in range(len(triples_sorted) - 1):
            if triples_sorted[i + 1] != triples_sorted[i] + 1:
                return None

        plane_len = len(triples_sorted)
        base_triple_cards = plane_len * 3

        if n == base_triple_cards:
            # 纯飞机
            return ClassifiedType(
                CardType.AIRPLANE,
                main_rank=triples_sorted[-1],
                length=plane_len,
            )

        # 计算翅膀部分
        # 拆掉三张
        remain_counts = counts.copy()
        for r in triples_sorted:
            remain_counts[r] -= 3
            if remain_counts[r] == 0:
                del remain_counts[r]

        remain_total = sum(remain_counts.values())

        # 带单：数量 = 飞机长度
        if remain_total == plane_len:
            # 不要求单牌点数不同
            return ClassifiedType(
                CardType.AIRPLANE_SINGLE,
                main_rank=triples_sorted[-1],
                length=plane_len,
            )

        # 带对：数量 = 飞机长度 * 2
        if remain_total == plane_len * 2:
            # 所有剩余牌必须是对子
            if all(cnt == 2 for cnt in remain_counts.values()):
                return ClassifiedType(
                    CardType.AIRPLANE_PAIR,
                    main_rank=triples_sorted[-1],
                    length=plane_len,
                )

        return None

    # ---------------- 对外主入口 ----------------

    @staticmethod
    def classify_type(cards: List[Card]) -> Optional[ClassifiedType]:
        """
        识别牌型：
          - 返回 ClassifiedType
          - 返回 None 表示非法（包括四带二等）
        """
        if not cards:
            return None

        # 牌面按 rank 排序便于分析
        cards = sorted(cards, key=lambda c: c.rank)

        # 特殊：王炸
        ct = DouDiZhuRules._is_rocket(cards)
        if ct:
            return ct

        # 炸弹（注意：这里只允许纯四张，不能带牌）
        ct = DouDiZhuRules._is_bomb(cards)
        if ct:
            return ct

        # 单、对
        if len(cards) <= 2:
            ct = DouDiZhuRules._is_single(cards) or DouDiZhuRules._is_pair(cards)
            return ct

        # 三张 / 三带一 / 三带二
        ct = DouDiZhuRules._is_triple_or_with(cards)
        if ct:
            return ct

        # 顺子
        ct = DouDiZhuRules._is_straight(cards)
        if ct:
            return ct

        # 连对
        ct = DouDiZhuRules._is_double_sequence(cards)
        if ct:
            return ct

        # 飞机
        ct = DouDiZhuRules._is_airplane_and_wings(cards)
        if ct:
            return ct

        # 其它形态（特别是四带二）一律不合法
        return None

    @staticmethod
    def can_beat(prev: ClassifiedType, cur: ClassifiedType) -> bool:
        """
        判断 cur 是否能压住 prev
        """
        # 王炸最大
        if prev.type == CardType.ROCKET:
            return False
        if cur.type == CardType.ROCKET:
            return True

        # 炸弹可以压任意非炸弹/王炸
        if cur.type == CardType.BOMB:
            if prev.type != CardType.BOMB:
                return True
            # 炸弹对比
            return cur.main_rank > prev.main_rank

        # 非炸弹牌，不能压炸弹/王炸
        if prev.type == CardType.BOMB and cur.type != CardType.BOMB:
            return False

        # 类型不同，不能压
        if prev.type != cur.type:
            return False

        # 顺子、连对、飞机：长度必须一致
        if prev.type in (
            CardType.STRAIGHT,
            CardType.DOUBLE_SEQUENCE,
            CardType.AIRPLANE,
            CardType.AIRPLANE_SINGLE,
            CardType.AIRPLANE_PAIR,
        ):
            if prev.length != cur.length:
                return False

        # 比较主点数
        return cur.main_rank > prev.main_rank
