# -*- coding: utf-8 -*-
"""
统一动作生成模块
训练与推理共用的可用动作生成接口
"""

from app.game.rules import DouDiZhuRules


def get_all_valid_moves(dealer, player_id):
    """
    dealer: DealerReferee
    player_id: "human" / "bot1" / "bot2"

    返回所有合法动作（按训练时的规则一致）
    """

    obs = dealer.get_observation(player_id)
    hand = obs.my_hand

    # 列举所有可能组合（与 env.enumerate_all_moves 完全一致）
    moves = []

    # 单张
    for c in hand:
        moves.append([c])

    # 对子 / 三张 / 炸弹
    ranks = {}
    for c in hand:
        ranks.setdefault(c.rank, []).append(c)

    for r, lst in ranks.items():
        if len(lst) >= 2:
            moves.append(lst[:2])
        if len(lst) >= 3:
            moves.append(lst[:3])
        if len(lst) == 4:
            moves.append(lst[:4])

    # 可追加：顺子 / 连对 / 三带一 / 三带二 ……

    # last_non_pass 过滤
    last = obs.last_non_pass

    # 如果自己是下一轮出牌的人 → 不需要过滤（新一轮）
    if not last or last.player_id == player_id:
        return moves

    # 否则需要压牌
    last_ct = DouDiZhuRules.classify_type(last.cards)
    legal = []

    for m in moves:
        ct = DouDiZhuRules.classify_type(m)
        if ct and DouDiZhuRules.can_beat(last_ct, ct):
            legal.append(m)

    # 如果没有合适的动作 → PASS
    if not legal:
        return [[]]   # 空列表表示 PASS

    return legal
