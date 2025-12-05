# -*- coding: utf-8 -*-
"""
强化学习工具函数
"""

import numpy as np
import torch


def to_tensor(x):
    """自动转 tensor 到 GPU 或 CPU"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.tensor(x, dtype=torch.float32, device=device)


def pad_to_length(arr, length):
    """把数组补到固定长度"""
    out = list(arr)
    while len(out) < length:
        out.append(0.0)
    return np.array(out[:length], dtype=np.float32)


def set_seed(seed=42):
    """设置随机种子"""
    import random
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
