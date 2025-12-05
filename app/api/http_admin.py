from typing import Dict, Any
from fastapi import APIRouter, Query, HTTPException
from app.config import ADMIN_TOKEN
from app.game.runtime import dealer
from app.utils.helpers import cards_to_str

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/state")
def admin_state(token: str = Query(..., description="管理员 token")) -> Dict[str, Any]:
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="unauthorized")

    state = dealer.state
    players_info = {}
    for pid, ps in state.players.items():
        players_info[pid] = {
            "role": ps.role.value,
            "hand_count": len(ps.hand),
            "hand": [c.dict() for c in ps.hand],
        }

    history = [
        {"player_id": r.player_id, "cards": cards_to_str(r.cards), "action_type": r.action_type}
        for r in state.history
    ]

    return {
        "players": players_info,
        "bottom_cards": [c.dict() for c in state.bottom_cards],
        "landlord_id": state.landlord_id,
        "current_turn": state.current_turn,
        "history": history,
        "multiplier": state.multiplier,
        "game_over": state.game_over,
        "winner_side": state.winner_side,
    }
