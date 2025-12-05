# -*- coding: utf-8 -*-
"""
PPO 模型结构：MLP + LSTM 双路网络
- 输入：state 向量 (约 40 维)
- 输出：policy logits + value
"""

import torch
import torch.nn as nn


class PPOPolicy(nn.Module):
    def __init__(self, state_dim=40, hidden_dim=128, lstm_hidden=128):
        super().__init__()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ---- MLP 路径：提取手牌、历史等结构特征 ----
        self.mlp = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )

        # ---- LSTM 路径：提取时间特征（上一轮出牌趋势等） ----
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True
        )

        # ---- 合并输出 ----
        combined_dim = hidden_dim + lstm_hidden

        # Policy 输出（动作 logits）
        self.policy_head = nn.Sequential(
            nn.Linear(combined_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128)
        )

        # Value 输出（状态价值）
        self.value_head = nn.Sequential(
            nn.Linear(combined_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

        self.to(self.device)

    # ---------------------------------------------------------
    # 前向：obs.shape = (batch, state_dim)
    # LSTM 需要 (batch, seq=1, hidden_dim)
    # ---------------------------------------------------------
    def forward(self, obs, lstm_state=None):
        x = self.mlp(obs)                  # (batch, hidden_dim)
        x_lstm_in = x.unsqueeze(1)         # (batch, 1, hidden_dim)

        if lstm_state is None:
            output, lstm_state = self.lstm(x_lstm_in)
        else:
            output, lstm_state = self.lstm(x_lstm_in, lstm_state)

        lstm_out = output[:, -1, :]        # (batch, lstm_hidden)

        combined = torch.cat([x, lstm_out], dim=-1)

        logits = self.policy_head(combined)
        value = self.value_head(combined)

        return logits, value.squeeze(1), lstm_state

    # ---------------------------------------------------------
    # 动作文采样
    # ---------------------------------------------------------
    def act(self, obs, lstm_state=None):
        logits, value, lstm_state = self.forward(obs, lstm_state)
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        logprob = dist.log_prob(action)
        return (
            action.detach(),
            logprob.detach(),
            value.detach(),
            lstm_state
        )
