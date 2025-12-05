# -*- coding: utf-8 -*-
"""
运行时深度 AI 桥接层（更新版）
正式使用 dealer.get_all_valid_moves()
确保动作与训练一致
"""

from app.ai.engine_deeprl import DeepRL_AI


class RuntimeAIManager:
    def __init__(self, checkpoint="model/ppo_final.pt"):
        self.ai = DeepRL_AI(checkpoint)

    def get_ai_move(self, dealer, player_id):
        """
        返回深度 AI 选择的动作
        """

        # === 统一动作生成（关键） ===
        if hasattr(dealer, "get_all_valid_moves"):
            moves = dealer.get_all_valid_moves(player_id)
        else:
            # 如果用户没有使用补丁类，则 fallback
            moves = dealer.get_all_valid_moves(player_id)

        if len(moves) == 0:
            return []

        obs = dealer.get_observation(player_id)

        chosen = self.ai.choose_action(obs, moves)

        # fallback：如果 chosen 非法
        if chosen not in moves:
            chosen = moves[0]

        return chosen
