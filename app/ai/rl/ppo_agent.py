# -*- coding: utf-8 -*-
"""
PPO 算法实现
- 计算 clipped policy loss
- 计算 value loss
- 计算 entropy（鼓励探索）
- 更新模型
"""

import torch
import torch.nn as nn
import torch.optim as optim


class PPOAgent:
    def __init__(
        self,
        policy_model,
        lr=3e-4,
        gamma=0.99,
        lam=0.95,
        clip_ratio=0.2,
        update_epochs=10,
        entropy_coef=0.01,
        value_coef=0.5,
        max_grad_norm=0.5
    ):
        self.policy = policy_model
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)

        self.gamma = gamma
        self.lam = lam
        self.clip_ratio = clip_ratio
        self.update_epochs = update_epochs
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---------------------------------------------------------
    # 使用 PPO 更新参数
    # ---------------------------------------------------------
    def update(self, states, actions, old_logprobs, advantages, returns):
        for _ in range(self.update_epochs):
            logits, values, _ = self.policy.forward(states)
            dist = torch.distributions.Categorical(logits=logits)

            logprobs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            ratios = torch.exp(logprobs - old_logprobs)

            # clipped surrogate objective
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.clip_ratio, 1 + self.clip_ratio) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            # value loss
            value_loss = (returns - values).pow(2).mean()

            # 总损失
            loss = (
                policy_loss
                + self.value_coef * value_loss
                - self.entropy_coef * entropy
            )

            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
            self.optimizer.step()

        return (
            loss.item(),
            policy_loss.item(),
            value_loss.item(),
            entropy.item()
        )
