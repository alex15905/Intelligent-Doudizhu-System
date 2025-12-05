from typing import List
from app.ai.engine_base import AIEngineBase
from app.models.card import Card, Observation
from app.game.rules import DouDiZhuRules
from app.utils.logger import logger
from app.utils.helpers import cards_to_str


class RuleBasedAIEngine(AIEngineBase):
    """
    非常简单的规则 AI：
      - 如果当前没有“需要被压”的牌（last_non_pass 为 None，或 last_non_pass 是自己出的），
        则执行“起牌策略”：出手里最小的一张单牌。
      - 否则，如果最后一手是单牌，就尝试用手里比它大的最小单牌压住。
      - 压不住就 PASS。
    这个只是占位，保证系统可以跑通，后续可以换成更高级的智能体。
    """

    def choose_action(self, obs: Observation) -> List[Card]:
        hand = sorted(obs.my_hand, key=lambda c: c.rank)
        if not hand:
            return []

        # 使用 last_non_pass 作为“真正需要被压”的那一手
        last_play = obs.last_non_pass

        # 如果没有 last_non_pass，或者 last_non_pass 就是自己出的，
        # 说明这一轮轮到自己“重新起牌”，可以随便出（这里出最小单牌）。
        if (not last_play) or (last_play.player_id == obs.my_id):
            card = hand[0]
            logger.info(
                "AI(%s) starts new round with smallest single: %s",
                obs.my_id,
                cards_to_str([card]),
            )
            return [card]

        # 识别上一手牌型
        prev_ct = DouDiZhuRules.classify_type(last_play.cards)
        if prev_ct is None:
            # 理论上不会发生，直接 PASS
            logger.info("AI(%s) PASS (prev invalid)", obs.my_id)
            return []

        # 这里只处理上一手是单牌的情况，其它型先都 PASS
        if prev_ct.type.name != "SINGLE":
            logger.info(
                "AI(%s) PASS (cannot handle type=%s yet)", obs.my_id, prev_ct.type
            )
            return []

        # 找一张比上家大的最小牌
        for c in hand:
            if c.rank > prev_ct.main_rank:
                logger.info(
                    "AI(%s) beats single with: %s", obs.my_id, cards_to_str([c])
                )
                return [c]

        # 压不住，PASS
        logger.info("AI(%s) PASS (no bigger single)", obs.my_id)
        return []
