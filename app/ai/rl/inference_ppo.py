# -*- coding: utf-8 -*-
"""
PPO 推理模块
将训练好的模型接入你的斗地主系统：
- choose_action(obs)
"""

import torch
from app.ai.rl.model_ppo import PPOPolicy
from app.game.rules import DouDiZhuRules
from app.models.card import Card


class DeepRLInferenceEngine:
    def __init__(self, checkpoint_path="model/ppo_checkpoint.pt"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 模型初始化
        self.model = PPOPolicy()
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        self.lstm_state = None

    # ---------------------------------------------------------
    # 状态编码（与你训练时一致）
    # ---------------------------------------------------------
    def encode_state(self, obs):
        vec = []

        hand = sorted(obs.my_hand, key=lambda c: (c.rank, c.suit))
        for c in hand:
            vec.append(c.rank / 17.0)
        while len(vec) < 20:
            vec.append(0.0)

        last = obs.last_non_pass
        if last:
            for c in last.cards:
                vec.append(c.rank / 17.0)
            while len(vec) < 40:
                vec.append(0.0)
        else:
            while len(vec) < 40:
                vec.append(0.0)

        return torch.tensor([vec], dtype=torch.float32, device=self.device)

    # ---------------------------------------------------------
    # 主入口：选择出牌
    # ---------------------------------------------------------
    def choose_action(self, obs):
        state = self.encode_state(obs)

        logits, value, self.lstm_state = self.model.forward(state, self.lstm_state)

        # 生成候选动作
        from app.game.dealer import DealerReferee
        # 注意：obs 中没有 dealer，只能重新生成
        # 推理阶段你会传入 obs 并外部提供合法动作与比较逻辑

        # 这里仅作示范，训练接入时你会提供 moves
        # 推理版 AI 不负责规则 → 因为你现有系统已经负责

        return []  # TODO: 训练接入时由 runtime 提供候选动作

