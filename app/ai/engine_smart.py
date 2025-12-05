# -*- coding: utf-8 -*-
"""
SmartAI: 兼容旧接口的“智能 AI 包装层”

当前实现逻辑：
- 保留原来的类名 SmartAI，保证 ws_game 等旧代码无需修改
- 外层再提供 SmartAIEngine 这个名字，兼容 runtime.py 里的导入：
    from app.ai.engine_smart import SmartAIEngine

- 对外接口：
    SmartAIEngine.choose_action(obs) -> List[Card]

- 内部不再使用旧的 simulate_future 搜索（避免 list.remove 错误）
- 统一调用深度强化学习模型 DeepRL_AI 来决策出牌
"""

import logging
from typing import List

from app.ai.engine_deeprl import DeepRL_AI
from app.game.rules import DouDiZhuRules
from app.models.card import Card

logger = logging.getLogger("doudizhu")


class SmartAI:
    def __init__(self, *args, **kwargs):
        """
        兼容原有调用方式：
        - 之前可能是 SmartAI("bot1") 或 SmartAI(player_id="bot1")
        - 这里用 *args, **kwargs 接住所有参数，避免因为签名变化导致报错
        """

        # 记录一个名字，方便日志打印
        if args:
            self.name = str(args[0])
        else:
            self.name = str(kwargs.get("name", "bot"))

        # 模型 checkpoint 路径，可通过 kwargs 覆盖
        checkpoint = kwargs.get("checkpoint", "model/ppo_final.pt")

        logger.info(
            f"SmartAI({self.name}) 初始化，内部使用 DeepRL_AI，checkpoint={checkpoint}"
        )

        # 内部真正使用的深度强化学习模型
        self.rl_ai = DeepRL_AI(checkpoint=checkpoint)

    # ---------------------------------------------------------
    # 对外接口：选择出牌动作
    # ---------------------------------------------------------
    def choose_action(self, obs):
        """
        obs: Observation（由 DealerReferee.get_observation 返回）

        返回值：List[Card]，即要出的牌
        """
        # 打印一下当前手牌，保持和原先日志风格类似
        hand_str = " ".join(str(c) for c in obs.my_hand)
        logger.info(f"SmartAI({self.name}) thinking... hand={hand_str}")

        # 生成合法动作列表（和训练时规则保持一致：单张 / 对子 / 三张 / 炸弹）
        moves = self._generate_legal_moves(obs)

        if not moves:
            # 没有任何合法动作，只能 PASS
            return []

        # 交给深度模型来在这些合法动作中做选择
        chosen = self.rl_ai.choose_action(obs, moves)

        # 保险起见，如果模型返回了一个不在 moves 里的动作，就用第一个合法动作兜底
        if chosen not in moves:
            logger.warning(
                f"SmartAI({self.name}) 模型返回了非法动作，使用 fallback 第一个合法动作"
            )
            chosen = moves[0]

        return chosen

    # ---------------------------------------------------------
    # 生成合法动作（与 RL 训练环境中 env_doudizhu 的逻辑保持一致）
    # ---------------------------------------------------------
    def _generate_legal_moves(self, obs) -> List[List[Card]]:
        """
        根据当前观察 obs 和规则，生成所有合法动作。
        - 目前支持：单张 / 对子 / 三张 / 炸弹
        - 如果有 last_non_pass，需能够压过它
        """
        hand = sorted(obs.my_hand, key=lambda c: (c.rank, c.suit))

        # 1) 枚举所有可能牌型：单张 / 对子 / 三张 / 炸弹
        all_moves: List[List[Card]] = self._enumerate_basic_moves(hand)

        # 2) 如果桌面上有上一手非 PASS 出牌，且不是自己出的，则需要能压过它
        last = obs.last_non_pass
        if last and last.player_id != obs.my_id:
            last_ct = DouDiZhuRules.classify_type(last.cards)
            filtered = []
            for m in all_moves:
                ct = DouDiZhuRules.classify_type(m)
                if ct and DouDiZhuRules.can_beat(last_ct, ct):
                    filtered.append(m)
            if len(filtered) == 0:
                # 没有能压住的牌 → 只能 PASS
                return [[]]
            return filtered

        # 3) 新一轮出牌（自己接管），可以出任意牌型
        return all_moves

    # ---------------------------------------------------------
    # 不考虑是否能压牌，只列举手牌中的所有基础牌型
    # ---------------------------------------------------------
    def _enumerate_basic_moves(self, hand: List[Card]) -> List[List[Card]]:
        moves: List[List[Card]] = []

        # 单张
        for c in hand:
            moves.append([c])

        # 按 rank 分组，枚举对子 / 三张 / 炸弹
        ranks = {}
        for c in hand:
            ranks.setdefault(c.rank, []).append(c)

        for r, lst in ranks.items():
            if len(lst) >= 2:
                moves.append(lst[:2])
            if len(lst) >= 3:
                moves.append(lst[:3])
            if len(lst) == 4:
                moves.append(lst[:4])

        # TODO：如果你希望后面可以继续扩展顺子、连对、三带一（三带二）等牌型，
        # 但要注意和 env_doudizhu / DouDiZhuRules 中的牌型识别保持一致。

        return moves


# =========================================================
# 兼容旧代码的包装类：SmartAIEngine
# =========================================================
class SmartAIEngine:
    """
    这是 runtime.py 里期望导入的名字：
        from app.ai.engine_smart import SmartAIEngine

    它对外只暴露一个方法：
        choose_action(obs) -> List[Card]

    内部直接委托给上面的 SmartAI（已经接入 DeepRL_AI）
    """

    def __init__(self, checkpoint: str = "model/ppo_final.pt", name: str = "bot"):
        self.smart_ai = SmartAI(name=name, checkpoint=checkpoint)

    def choose_action(self, obs):
        return self.smart_ai.choose_action(obs)
