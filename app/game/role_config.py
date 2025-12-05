# -*- coding: utf-8 -*-
"""
全局人类身份配置：
- human_role = landlord / farmer
- 默认人类是地主（landlord）
"""

from enum import Enum


class HumanRole(str, Enum):
    LANDLORD = "landlord"
    FARMER = "farmer"


# 默认：人类是地主
_HUMAN_ROLE: HumanRole = HumanRole.LANDLORD


def set_human_role(role: str) -> None:
    """
    设置人类身份：
    - "landlord"：人类做地主
    - "farmer"：人类做农民（地主改为机器人）
    其他值一律当成 landlord 处理
    """
    global _HUMAN_ROLE
    if role == "farmer":
        _HUMAN_ROLE = HumanRole.FARMER
    else:
        _HUMAN_ROLE = HumanRole.LANDLORD


def get_human_role() -> str:
    """
    返回当前人类身份字符串："landlord" 或 "farmer"
    """
    return _HUMAN_ROLE.value
