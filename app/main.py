# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import http_misc, http_admin, ws_game, http_role

app = FastAPI(title="DouDiZhuAI")

# 简单放开 CORS，方便前端本地调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 原有路由
app.include_router(http_misc.router)
app.include_router(http_admin.router)
app.include_router(ws_game.router)

# 新加的人类身份配置路由
app.include_router(http_role.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
