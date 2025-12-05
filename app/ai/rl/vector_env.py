# -*- coding: utf-8 -*-
"""
多进程并行环境 (Vectorized Environment)
用于 PPO 大规模训练。
"""

import multiprocessing as mp
import numpy as np
import logging

from .env_doudizhu import DouDiZhuEnv


def worker(remote, parent_remote):
    """
    每个子进程的入口。
    在这里直接全局关闭 logging，避免刷屏影响训练进度条。
    """
    parent_remote.close()

    # 彻底关闭本进程所有日志输出
    logging.disable(logging.CRITICAL)

    env = DouDiZhuEnv()

    while True:
        cmd, data = remote.recv()

        if cmd == "reset":
            obs, info = env.reset()
            remote.send((obs, info))

        elif cmd == "step":
            obs, reward, done, info = env.step(data)
            if done:
                # 结束后自动重置一局，方便连续训练
                obs, info_reset = env.reset()
                info["reset"] = True
            remote.send((obs, reward, done, info))

        elif cmd == "close":
            remote.close()
            break

        else:
            raise NotImplementedError


class VectorEnv:
    def __init__(self, num_envs=16):
        self.num_envs = num_envs

        self.remotes, self.work_remotes = zip(*[mp.Pipe() for _ in range(num_envs)])
        self.processes = []

        for wr, r in zip(self.work_remotes, self.remotes):
            p = mp.Process(target=worker, args=(wr, r))
            p.daemon = True
            p.start()
            wr.close()
            self.processes.append(p)

    # ---------------------------------------------------------
    def reset(self):
        for remote in self.remotes:
            remote.send(("reset", None))

        results = [remote.recv() for remote in self.remotes]
        obs, info = zip(*results)
        return np.array(obs), info

    # ---------------------------------------------------------
    def step(self, actions):
        for remote, act in zip(self.remotes, actions):
            remote.send(("step", act))

        results = [remote.recv() for remote in self.remotes]
        obs, rewards, dones, infos = zip(*results)
        return (
            np.array(obs),
            np.array(rewards),
            np.array(dones),
            infos,
        )

    # ---------------------------------------------------------
    def close(self):
        for remote in self.remotes:
            remote.send(("close", None))

        for p in self.processes:
            p.join()
