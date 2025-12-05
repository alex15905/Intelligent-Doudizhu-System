# -*- coding: utf-8 -*-
"""
PPO Rollout Buffer
用于存储一个 rollout 内的样本，并计算 GAE 优势和 returns。
"""

import numpy as np
import torch


class RolloutBuffer:
    def __init__(self, buffer_size, state_dim, action_dim):
        self.buffer_size = buffer_size
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.states = np.zeros((buffer_size, state_dim), dtype=np.float32)
        self.actions = np.zeros((buffer_size,), dtype=np.int64)
        self.rewards = np.zeros((buffer_size,), dtype=np.float32)
        self.logprobs = np.zeros((buffer_size,), dtype=np.float32)
        self.values = np.zeros((buffer_size,), dtype=np.float32)
        self.dones = np.zeros((buffer_size,), dtype=np.float32)

        self.ptr = 0
        self.path_start_idx = 0

    def store(self, state, action, reward, value, logprob, done):
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.values[self.ptr] = value
        self.logprobs[self.ptr] = logprob
        self.dones[self.ptr] = done
        self.ptr += 1

    def is_full(self):
        return self.ptr >= self.buffer_size

    def finish_path(self, last_value=0.0, gamma=0.99, lam=0.95):
        """
        使用 GAE 计算优势函数。
        """
        path_end = self.ptr
        rewards = self.rewards[self.path_start_idx : path_end]
        values = self.values[self.path_start_idx : path_end]
        dones = self.dones[self.path_start_idx : path_end]

        values = np.append(values, last_value)

        deltas = rewards + gamma * values[1:] * (1 - dones) - values[:-1]
        adv = np.zeros_like(deltas)

        last_adv = 0
        for t in reversed(range(len(deltas))):
            last_adv = deltas[t] + gamma * lam * (1 - dones[t]) * last_adv
            adv[t] = last_adv

        returns = adv + values[:-1]

        self.advantages = adv
        self.returns = returns
        self.path_start_idx = self.ptr

    def get(self):
        """
        返回所有样本，并归一化优势
        """
        adv = self.advantages
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        return (
            torch.tensor(self.states, dtype=torch.float32, device=device),
            torch.tensor(self.actions, dtype=torch.long, device=device),
            torch.tensor(self.logprobs, dtype=torch.float32, device=device),
            torch.tensor(adv, dtype=torch.float32, device=device),
            torch.tensor(self.returns, dtype=torch.float32, device=device),
        )
