# -*- coding: utf-8 -*-
"""
PPO 训练脚本（可直接运行）
支持：
- 多进程并行环境
- PPO 更新
- TensorBoard
- tqdm 进度条
- GPU 加速（如果 torch.cuda.is_available 为 True）
"""

import os
import time
import logging
import torch
import numpy as np
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from app.ai.rl.vector_env import VectorEnv
from app.ai.rl.model_ppo import PPOPolicy
from app.ai.rl.ppo_agent import PPOAgent
from app.ai.rl.buffer import RolloutBuffer


# ---------------------------------------------------------
# 配置
# ---------------------------------------------------------
NUM_ENVS = 32              # 你的 7900X 完全能跑 32 环境
ROLLOUT_STEPS = 128        # 每个环境 rollout 步数
TOTAL_EPISODES = 1_000_000  # 一百万局
CHECKPOINT_INTERVAL = 50000
STATE_DIM = 40
ACTION_DIM = 128           # 策略输出维度 (与策略网络一致)


def create_dirs():
    os.makedirs("logs/ppo_train", exist_ok=True)
    os.makedirs("model", exist_ok=True)


# ---------------------------------------------------------
# 主训练函数
# ---------------------------------------------------------
def train():
    create_dirs()

    # 关掉训练时的详细日志，避免刷屏，把 tqdm 顶掉
    logging.getLogger("doudizhu").setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")

    # 多环境加速
    envs = VectorEnv(NUM_ENVS)

    # 初始化模型
    policy = PPOPolicy(state_dim=STATE_DIM, hidden_dim=128, lstm_hidden=128)
    agent = PPOAgent(policy)

    # TensorBoard
    writer = SummaryWriter("logs/ppo_train")

    # Rollout Buffer
    buffer_size = NUM_ENVS * ROLLOUT_STEPS
    buffer = RolloutBuffer(buffer_size, STATE_DIM, 1)

    # 重置所有环境
    obs, _ = envs.reset()

    global_step = 0
    episode_count = 0

    pbar = tqdm(total=TOTAL_EPISODES, desc="训练进度（按局数）", ncols=120)

    # ---------------------------------------------------------
    # 训练循环
    # ---------------------------------------------------------
    while episode_count < TOTAL_EPISODES:

        # rollout steps
        for t in range(ROLLOUT_STEPS):
            global_step += NUM_ENVS

            # 模型动作
            obs_tensor = torch.tensor(obs, dtype=torch.float32, device=device)

            logits, value, _ = policy.forward(obs_tensor)
            dist = torch.distributions.Categorical(logits=logits)
            action_tensor = dist.sample()

            actions = action_tensor.cpu().numpy()
            logprobs = dist.log_prob(action_tensor).detach().cpu().numpy()
            values = value.detach().cpu().numpy()

            # 多环境步进
            next_obs, rewards, dones, infos = envs.step(actions)

            # 收集经验
            for i in range(NUM_ENVS):
                buffer.store(
                    obs[i],
                    actions[i],
                    rewards[i],
                    values[i],
                    logprobs[i],
                    dones[i],
                )

                if dones[i]:
                    episode_count += 1
                    pbar.update(1)

            obs = next_obs

        # 计算 GAE
        last_value = 0.0
        buffer.finish_path(last_value)

        # 采集 rollout
        states, actions_t, old_logprobs, advantages, returns = buffer.get()

        # PPO 更新
        loss, ploss, vloss, entropy = agent.update(
            states, actions_t, old_logprobs, advantages, returns
        )

        # 记录日志
        writer.add_scalar("loss/total", loss, global_step)
        writer.add_scalar("loss/policy", ploss, global_step)
        writer.add_scalar("loss/value", vloss, global_step)
        writer.add_scalar("loss/entropy", entropy, global_step)
        writer.add_scalar("train/episode_count", episode_count, global_step)

        # 立刻 flush 一次，让 TensorBoard 更接近实时
        writer.flush()

        # 保存 checkpoint
        if episode_count > 0 and episode_count % CHECKPOINT_INTERVAL == 0:
            cp_path = f"model/ppo_checkpoint_{episode_count}.pt"
            torch.save(policy.state_dict(), cp_path)
            print(f"[INFO] Saved checkpoint: {cp_path}")

        # 清空 buffer 指针，准备下一轮收集
        buffer.ptr = 0
        buffer.path_start_idx = 0

    pbar.close()
    envs.close()
    writer.close()

    torch.save(policy.state_dict(), "model/ppo_final.pt")
    print("[INFO] Final model saved: model/ppo_final.pt")


if __name__ == "__main__":
    train()
