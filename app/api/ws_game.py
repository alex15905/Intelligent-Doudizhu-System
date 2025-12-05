from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.game.runtime import dealer, ai_engine
from app.models.card import Card
from app.utils.logger import logger
from app.utils.helpers import cards_to_str

router = APIRouter()

# 一个 room_id 对应一个 human 连接
human_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/game/{room_id}")
async def ws_game(websocket: WebSocket, room_id: str):
    await websocket.accept()
    human_connections[room_id] = websocket
    logger.info("Human connected room_id=%s", room_id)

    # 开新局
    dealer.start_new_game()
    obs = dealer.get_observation("human")

    # 初始化消息：带上当前回合
    await websocket.send_json(
        {
            "type": "init",
            "you": obs.my_id,
            "hand": [c.dict() for c in obs.my_hand],
            "landlord_id": dealer.state.landlord_id,
            "current_turn": dealer.state.current_turn,
        }
    )

    # 如果开局就轮到 AI（目前地主固定 human，不会触发），走一遍 AI
    await drive_ai_until_human(room_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "play":
                cards_data = data.get("cards", [])
                cards = [Card(**c) for c in cards_data]
                ok, err = dealer.play_cards("human", cards)

                # 给出牌请求本身的反馈
                await websocket.send_json(
                    {"type": "play_result", "ok": ok, "error": err}
                )

                # 广播人类出牌（含当前回合信息）
                await broadcast_state(room_id, "human", cards, ok, err)

                # 若游戏结束，广播 game_over
                if dealer.state.game_over:
                    await send_game_over(room_id)
                    continue

                # 轮到 AI 的话，一路驱动到再次轮到 human 或结束
                await drive_ai_until_human(room_id)

            elif msg_type == "pass":
                ok, err = dealer.play_cards("human", [])
                await websocket.send_json(
                    {"type": "play_result", "ok": ok, "error": err}
                )
                await broadcast_state(room_id, "human", [], ok, err)

                if dealer.state.game_over:
                    await send_game_over(room_id)
                    continue

                await drive_ai_until_human(room_id)

    except WebSocketDisconnect:
        logger.info("Human disconnected room_id=%s", room_id)
        human_connections.pop(room_id, None)


async def drive_ai_until_human(room_id: str):
    """
    如果轮到 bot，就循环调用 AI，直到轮到 human 或游戏结束。
    每次 AI 出牌后，都会向前端发送 bot_play 消息，附带当前回合信息。
    """
    ws = human_connections.get(room_id)
    while (
        not dealer.state.game_over
        and dealer.state.current_turn in ("bot1", "bot2")
    ):
        pid = dealer.state.current_turn
        obs = dealer.get_observation(pid)
        ai_cards = ai_engine.choose_action(obs)
        ok, err = dealer.play_cards(pid, ai_cards)
        logger.info(
            "AI %s play result: ok=%s, err=%s, cards=%s",
            pid,
            ok,
            err,
            cards_to_str(ai_cards),
        )

        # 通知前端 AI 出牌，带当前回合信息（此时 current_turn 已经被 play_cards 更新为下一家）
        if ws:
            await ws.send_json(
                {
                    "type": "bot_play",
                    "player_id": pid,
                    "cards": [c.dict() for c in ai_cards],
                    "ok": ok,
                    "error": err,
                    "current_turn": dealer.state.current_turn,
                    "multiplier": dealer.state.multiplier,
                }
            )

        if dealer.state.game_over:
            await send_game_over(room_id)
            break

    # 循环结束时，要么轮到 human，要么游戏结束


async def broadcast_state(room_id: str, player_id: str, cards, ok: bool, err):
    """
    向前端广播 human 的出牌结果，带上当前回合信息。
    """
    ws = human_connections.get(room_id)
    if not ws:
        return
    await ws.send_json(
        {
            "type": "human_play",
            "player_id": player_id,
            "cards": [c.dict() for c in cards],
            "ok": ok,
            "error": err,
            "current_turn": dealer.state.current_turn,
            "multiplier": dealer.state.multiplier,
        }
    )


async def send_game_over(room_id: str):
    ws = human_connections.get(room_id)
    if not ws:
        return
    state = dealer.state
    await ws.send_json(
        {
            "type": "game_over",
            "winner_side": state.winner_side,
            "landlord_id": state.landlord_id,
            "multiplier": state.multiplier,
        }
    )
