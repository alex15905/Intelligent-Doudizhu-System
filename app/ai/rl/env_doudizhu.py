# -*- coding: utf-8 -*-
"""
斗地主强化学习环境（self-play）
用于 PPO / RL 模型训练。
与 DealerReferee 深度适配。
"""

import random
import numpy as np
from typing import Tuple, List

from app.game.dealer import DealerReferee
from app.models.card import Card
from app.game.rules import DouDiZhuRules


class DouDiZhuEnv:
    """
    强化学习环境，支持：
    - reset()
    - step(action_index)
    - action_index 为“从候选动作列表中选择第 idx 个”
    - 自动推进三名玩家（self-play）
    """

    def __init__(self):
        self.dealer = DealerReferee()
        self.current_player = "human"
        self.last_obs = None
        self.done = False
        self.reward = 0.0
        self.available_moves: List[List[Card]] = []
        self.ai_ids = ["human", "bot1", "bot2"]

    # ---------------------------------------------------------
    # 重置环境
    # ---------------------------------------------------------
    def reset(self) -> Tuple[np.ndarray, dict]:
        """开始新局，返回初始状态表示"""
        self.dealer.start_new_game()
        self.current_player = "human"
        self.done = False
        self.reward = 0.0

        obs = self.dealer.get_observation(self.current_player)

        # 生成合法动作
        self.available_moves = self.generate_legal_moves(obs)

        self.last_obs = obs
        state_vec = self.encode_state(obs)

        return state_vec, {"moves": self.available_moves}

    # ---------------------------------------------------------
    # 执行动作（action_index 为候选动作中的索引）
    # ---------------------------------------------------------
    def step(self, action_index: int) -> Tuple[np.ndarray, float, bool, dict]:
        if self.done:
            return self.encode_state(self.last_obs), 0.0, True, {}

        moves = self.available_moves
        if len(moves) == 0:
            # 无动作 → 视为 PASS
            chosen = []
        else:
            if action_index < 0 or action_index >= len(moves):
                # 非法 index → PASS
                chosen = []
            else:
                chosen = moves[action_index]

        # 执行当前玩家出牌
        ok, err = self.dealer.play_cards(self.current_player, chosen)

        if not ok:
            # 非法出牌 → 惩罚，保持状态不变
            reward = -5.0
            next_obs = self.last_obs
            self.available_moves = moves
            return self.encode_state(next_obs), reward, False, {
                "moves": moves,
                "error": err,
            }

        # 判断是否结束
        if self.dealer.state.game_over:
            reward = self._calc_final_reward(self.current_player)
            self.done = True
            obs = self.dealer.get_observation(self.current_player)
            return self.encode_state(obs), reward, True, {
                "winner": self.dealer.state.winner_side
            }

        # 推动另外两家自动出牌（self-play）
        reward = 0.0
        for _ in range(2):
            pid = self.dealer.state.current_turn
            obs_ai = self.dealer.get_observation(pid)
            ai_moves = self.generate_legal_moves(obs_ai)

            if len(ai_moves) == 0:
                ai_choice = []
            else:
                idx = random.randrange(len(ai_moves))
                ai_choice = ai_moves[idx]

            self.dealer.play_cards(pid, ai_choice)

            if self.dealer.state.game_over:
                reward = self._calc_final_reward(self.current_player)
                self.done = True
                obs = self.dealer.get_observation(self.current_player)
                return self.encode_state(obs), reward, True, {
                    "winner": self.dealer.state.winner_side
                }

        # 回到 human 回合
        self.current_player = self.dealer.state.current_turn
        obs = self.dealer.get_observation(self.current_player)
        self.available_moves = self.generate_legal_moves(obs)

        self.last_obs = obs
        state_vec = self.encode_state(obs)

        return state_vec, reward, False, {"moves": self.available_moves}

    # ---------------------------------------------------------
    # 终局奖励计算
    # ---------------------------------------------------------
    def _calc_final_reward(self, my_id: str) -> float:
        winner = self.dealer.state.winner_side
        my_role = self.dealer.state.players[my_id].role.value  # "landlord" / "farmer"

        if winner == "landlord" and my_role == "landlord":
            return 10.0
        if winner == "farmers" and my_role == "farmer":
            return 10.0
        return -10.0

    # ---------------------------------------------------------
    # 生成合法候选动作
    # ---------------------------------------------------------
    def generate_legal_moves(self, obs) -> List[List[Card]]:
        """
        根据当前观察 obs 和规则，生成所有合法动作（不含 PASS 过滤逻辑时的 PASS）。
        部分逻辑与训练时使用的一致。
        """
        hand = sorted(obs.my_hand, key=lambda c: (c.rank, c.suit))

        # 所有可能动作（单张、对子、三张、炸弹）
        all_moves = self.enumerate_all_moves(hand)

        # 是否需要压过 last_non_pass？
        last = obs.last_non_pass
        if last and last.player_id != obs.my_id:
            last_ct = DouDiZhuRules.classify_type(last.cards)
            filtered = []
            for m in all_moves:
                ct = DouDiZhuRules.classify_type(m)
                if ct and DouDiZhuRules.can_beat(last_ct, ct):
                    filtered.append(m)
            if len(filtered) == 0:
                # 没有能压住的牌 → PASS
                return [[]]
            return filtered

        # 新一轮出牌 → 允许任意牌型
        return all_moves

    # ---------------------------------------------------------
    # 列举所有出牌动作（不考虑是否能压牌）
    # 当前仅实现：单张 / 对子 / 三张 / 炸弹
    # ---------------------------------------------------------
    def enumerate_all_moves(self, hand: List[Card]) -> List[List[Card]]:
        moves: List[List[Card]] = []

        # 单张
        for c in hand:
            moves.append([c])

        # 对子 / 三张 / 炸弹
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

        # TODO: 可继续扩展顺子、连对、三带一/二等复杂牌型

        return moves

    # ---------------------------------------------------------
    # 状态编码（obs → 神经网络输入）
    # 固定 40 维：前 20 维手牌，后 20 维 last_non_pass
    # ---------------------------------------------------------
    def encode_state(self, obs) -> np.ndarray:
        """
        把 Observation 编码成固定大小向量（40 维）：
        - 前 20 维：自己的手牌（rank / 17，补零到 20）
        - 后 20 维：上一手非 PASS 出牌（rank / 17，补零到 20）
        """

        vec: List[float] = []

        # 1) 自己手牌
        hand = sorted(obs.my_hand, key=lambda c: (c.rank, c.suit))
        for c in hand:
            vec.append(c.rank / 17.0)
        while len(vec) < 20:
            vec.append(0.0)

        # 2) 上一手有效出牌（last_non_pass）
        last = obs.last_non_pass
        if last:
            for c in last.cards:
                vec.append(c.rank / 17.0)
            while len(vec) < 40:
                vec.append(0.0)
        else:
            while len(vec) < 40:
                vec.append(0.0)

        return np.array(vec, dtype=np.float32)
