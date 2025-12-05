# -*- coding: utf-8 -*-
"""
深度强化学习 AI（推理版）
用于真实斗地主对局：
- 如果有训练好的模型文件（ppo_final.pt），就加载它
- 如果没有，就使用随机初始化权重，并给出提示
"""

import os
import torch
from app.ai.rl.model_ppo import PPOPolicy


class DeepRL_AI:
    def __init__(self, checkpoint="model/ppo_final.pt"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 初始化 PPO 模型
        self.model = PPOPolicy()
        self.model.to(self.device)

        # 尝试加载 checkpoint，如果没有就随机初始化
        if os.path.exists(checkpoint):
            print(f"[DeepRL_AI] Loading trained model from: {checkpoint}")
            state_dict = torch.load(checkpoint, map_location=self.device)
            self.model.load_state_dict(state_dict)
        else:
            print(
                f"[DeepRL_AI] WARNING: checkpoint '{checkpoint}' not found. "
                f"Using randomly initialized weights (untrained model)."
            )

        self.model.eval()
        self.lstm_state = None

    # ---------------------------------------------------------
    # 状态编码（必须与训练时一致）
    # ---------------------------------------------------------
    def encode_state(self, obs):
        vec = []

        # 1) 我方手牌
        hand = sorted(obs.my_hand, key=lambda c: (c.rank, c.suit))
        for c in hand:
            vec.append(c.rank / 17.0)
        while len(vec) < 20:
            vec.append(0.0)

        # 2) last_non_pass
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
    # 选择动作（真实对战）
    # moves: List[List[Card]]
    # ---------------------------------------------------------
    def choose_action(self, obs, moves):
        """
        obs: Observation
        moves: 由 DealerReferee / get_all_valid_moves 生成的合法动作列表
        """
        if not moves:
            return []  # 只能 PASS

        state = self.encode_state(obs)

        with torch.no_grad():
            logits, value, self.lstm_state = self.model.forward(state, self.lstm_state)

        # logits: (1, 128)
        logits_np = logits.cpu().numpy()[0]

        # 截断到当前合法动作数量
        logits_np = logits_np[: len(moves)]

        # 贪心选最大值（推理阶段推荐）
        idx = int(logits_np.argmax())

        return moves[idx]
