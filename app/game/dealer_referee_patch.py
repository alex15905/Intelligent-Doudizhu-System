# -*- coding: utf-8 -*-
"""
为 DealerReferee 增加 get_all_valid_moves() 接口
（调用 dealer_moves 模块）
"""

from app.game.dealer import DealerReferee
from app.game.dealer_moves import get_all_valid_moves


class DealerRefereePatched(DealerReferee):
    """
    使用此类替换原 DealerReferee，
    增强其动作生成能力，使其兼容深度 AI。
    """

    def get_all_valid_moves(self, player_id):
        return get_all_valid_moves(self, player_id)
