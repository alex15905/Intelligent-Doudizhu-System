from typing import List, Optional
from app.game.constants import PLAYER_IDS, PlayerRole, CardType
from app.game.state import GameState
from app.game.deck import new_deck, shuffle_deck
from app.game.rules import DouDiZhuRules
from app.models.card import Card, ActionRecord, Observation
from app.utils.logger import logger
from app.utils.helpers import cards_to_str


class DealerReferee:
    """
    发牌 + 裁判 + 局面推进
    """

    def __init__(self) -> None:
        self.state: GameState = GameState.initial()

    # ---------- 发牌与开局 ----------

    def start_new_game(self) -> None:
        """重新开始一局，洗牌+发牌+确定地主（这里先固定 human 为地主，再根据配置做调整）。"""
        logger.info("Starting new game...")
        self.state = GameState.initial()

        deck = new_deck()
        shuffle_deck(deck)

        # 17 + 17 + 17 + 3 底牌
        hands = {
            "human": deck[0:17],
            "bot1": deck[17:34],
            "bot2": deck[34:51],
        }
        bottom = deck[51:]

        for pid in PLAYER_IDS:
            self.state.players[pid].hand = hands[pid]

        self.state.bottom_cards = bottom

        # 叫地主逻辑暂简化为 human，当地主（后面可能会被 _adjust_roles_for_human_choice 改掉）
        landlord_id = "human"
        self.state.landlord_id = landlord_id
        self.state.players[landlord_id].role = PlayerRole.LANDLORD
        for pid in PLAYER_IDS:
            if pid != landlord_id:
                self.state.players[pid].role = PlayerRole.FARMER

        # 地主先拿到底牌
        self.state.players[landlord_id].hand.extend(bottom)
        self.state.current_turn = landlord_id

        # 重置最后出牌记录
        self.state.last_play = None
        self.state.last_non_pass = None

        # ★★ 根据人类选择（地主/农民）调整身份和手牌 ★★
        self._adjust_roles_for_human_choice()

        # 最终日志（使用可能已被调整过的 landlord_id）
        logger.info(
            "New game started. Landlord=%s, bottom=%s",
            self.state.landlord_id,
            cards_to_str(self.state.bottom_cards),
        )

    # =========================================================
    # 按当前配置调整：人类当农民时，地主改为机器人 + 手牌互换
    # =========================================================
    def _adjust_roles_for_human_choice(self):
        """
        默认发牌逻辑仍然把人类当地主（兼容历史逻辑）：

        - 如果当前配置是 "landlord"：不做任何事
        - 如果当前配置是 "farmer"：
            * 从 bot1 / bot2 中挑一个做地主
            * 把“原本的人类地主手牌”跟这个机器人互换
            * 更新 GameState 中的 landlord_id / players[*].role / hand
            * 把 current_turn 设为新的地主
        """
        try:
            from app.game import role_config
        except Exception:
            # 理论上不会失败，失败就直接略过，不影响正常对局
            return

        human_role = role_config.get_human_role()
        if human_role != "farmer":
            # 配置是“人类当地主”，不用动
            return

        # 下面开始处理“人类当农民”的情况
        if not hasattr(self, "state") or self.state.landlord_id is None:
            return

        # 当前逻辑：发牌阶段一定把 human 设为地主
        # 如果将来你改了发牌逻辑，这里做个保护
        if self.state.landlord_id != "human":
            # 已经不是 human 当地主，就不要再乱动
            return

        # 从 bot1 / bot2 中选一个做地主
        candidate_ids = [pid for pid in ("bot1", "bot2") if pid in self.state.players]
        if not candidate_ids:
            return

        import random

        new_landlord = random.choice(candidate_ids)

        if "human" not in self.state.players or new_landlord not in self.state.players:
            return

        human_ps = self.state.players["human"]
        bot_ps = self.state.players[new_landlord]

        # 1) 交换手牌
        human_ps.hand, bot_ps.hand = bot_ps.hand, human_ps.hand

        # 2) 如果 DealerReferee 内部维护了 self.hands（有则一起换掉）
        if hasattr(self, "hands"):
            self.hands["human"], self.hands[new_landlord] = (
                self.hands.get(new_landlord, []),
                self.hands.get("human", []),
            )

        # 3) 角色标记调整
        human_ps.role = PlayerRole.FARMER
        bot_ps.role = PlayerRole.LANDLORD

        # 4) 地主标记 & 当前轮到谁
        self.state.landlord_id = new_landlord
        self.state.current_turn = new_landlord

        logger.info(
            "Human role set to FARMER. Switched landlord from 'human' to '%s'.",
            new_landlord,
        )

    # ---------- 视图生成 ----------

    def get_observation(self, player_id: str) -> Observation:
        """生成 AI/玩家可见的局部信息。"""
        ps = self.state.players[player_id]
        return Observation(
            my_id=player_id,
            my_hand=sorted(ps.hand, key=lambda c: (c.rank, c.suit)),
            public_history=self.state.history,
            landlord_id=self.state.landlord_id,
            current_turn=self.state.current_turn,
            last_play=self.state.last_play,
            last_non_pass=self.state.last_non_pass,
        )

    # ---------- 出牌逻辑 ----------

    def _remove_cards_from_hand(self, player_id: str, cards: List[Card]) -> bool:
        """从手牌中移除指定牌。失败返回 False。"""
        hand = self.state.players[player_id].hand
        tmp = hand.copy()

        for c in cards:
            found = False
            for h in tmp:
                if h.rank == c.rank and h.suit == c.suit:
                    tmp.remove(h)
                    found = True
                    break
            if not found:
                return False

        # 成功则替换
        self.state.players[player_id].hand = tmp
        return True

    def _check_game_over(self) -> None:
        """检查是否有玩家出完牌，更新胜负。"""
        if self.state.game_over:
            return
        for pid, ps in self.state.players.items():
            if len(ps.hand) == 0:
                # 该玩家获胜，判断阵营
                if ps.role == PlayerRole.LANDLORD:
                    self.state.winner_side = "landlord"
                else:
                    self.state.winner_side = "farmers"
                self.state.game_over = True
                logger.info(
                    "Game over. Winner side: %s (player=%s)",
                    self.state.winner_side,
                    pid,
                )
                break

    def play_cards(self, player_id: str, cards: List[Card]) -> (bool, Optional[str]):
        """
        某玩家尝试出牌：
          - cards 为空 => 视为 PASS
          - 返回 (ok, error_message)
        """
        if self.state.game_over:
            return False, "game_over"

        if player_id != self.state.current_turn:
            return False, "not_your_turn"

        # PASS
        if not cards:
            record = ActionRecord(player_id=player_id, cards=[], action_type="pass")
            self.state.history.append(record)
            # last_play 更新为 PASS，但 last_non_pass 不变
            self.state.last_play = record
            logger.info("Player %s PASS", player_id)
            self._advance_turn()
            return True, None

        # 1. 确认牌在手上
        if not self._remove_cards_from_hand(player_id, cards):
            return False, "cards_not_in_hand"

        # 2. 识别牌型
        ct = DouDiZhuRules.classify_type(cards)
        if ct is None:
            # 还原手牌
            self.state.players[player_id].hand.extend(cards)
            return False, "invalid_type"

        # 3. 比较是否可以压住上一手“真正出牌”
        last = self.state.last_non_pass
        if last is not None and last.player_id != player_id:
            prev_ct = DouDiZhuRules.classify_type(last.cards)
            if prev_ct is not None:
                if not DouDiZhuRules.can_beat(prev_ct, ct):
                    # 还原手牌
                    self.state.players[player_id].hand.extend(cards)
                    return False, "cannot_beat"

        # 4. 合法出牌，记录
        record = ActionRecord(player_id=player_id, cards=cards, action_type="play")
        self.state.history.append(record)
        # last_play 和 last_non_pass 都更新为本次出牌
        self.state.last_play = record
        self.state.last_non_pass = record

        logger.info(
            "Player %s plays: %s, type=%s",
            player_id,
            cards_to_str(cards),
            ct,
        )

        # 5. 炸弹/王炸倍数
        if ct.type in (CardType.BOMB, CardType.ROCKET):
            self.state.multiplier *= 2
            logger.info("Multiplier doubled to %d", self.state.multiplier)

        # 6. 检查是否结束
        self._check_game_over()

        # 7. 轮到下一家（如果还没结束）
        if not self.state.game_over:
            self._advance_turn()

        return True, None

    def _advance_turn(self) -> None:
        idx = PLAYER_IDS.index(self.state.current_turn)
        self.state.current_turn = PLAYER_IDS[(idx + 1) % len(PLAYER_IDS)]
        logger.info("Next turn: %s", self.state.current_turn)
