# -*- coding: utf-8 -*-
"""
人类身份切换接口：
- GET /config/human_role?role=landlord
- GET /config/human_role?role=farmer
"""

from fastapi import APIRouter, Query

from app.game import role_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/human_role")
async def set_human_role(role: str = Query("landlord")):
    """
    切换人类身份：
    - role=landlord：人类做地主（默认）
    - role=farmer：人类做农民（地主改为机器人）
    """
    if role not in ("landlord", "farmer"):
        return {
            "status": "error",
            "message": "role 必须是 landlord 或 farmer",
        }

    role_config.set_human_role(role)
    return {
        "status": "ok",
        "human_role": role_config.get_human_role(),
    }
