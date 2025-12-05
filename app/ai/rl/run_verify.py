# -*- coding: utf-8 -*-
"""
深度 AI 整体接入验证脚本
"""

from app.ai.rl.env_doudizhu import DouDiZhuEnv
from app.ai.engine_deeprl import DeepRL_AI
from app.game.dealer_referee_patch import DealerRefereePatched


def main():
    print("=== 测试深度模型加载 ===")
    ai = DeepRL_AI("model/ppo_final.pt")
    print("模型加载成功")

    print("=== 测试环境 reset ===")
    env = DouDiZhuEnv()
    obs, info = env.reset()
    print("环境 reset OK")

    print("=== 测试环境 step ===")
    obs, reward, done, info = env.step(0)
    print("环境 step OK")

    print("=== 测试 runtime 动作生成 ===")
    dealer = DealerRefereePatched()
    dealer.start_new_game()
    moves = dealer.get_all_valid_moves("bot1")
    print("动作数量:", len(moves))

    print("=== 测试 AI 推理 ===")
    obs = dealer.get_observation("bot1")
    chosen = ai.choose_action(obs, moves)
    print("推理动作:", chosen)

    print("=== 全部测试完成：你可以开始训练 + 接入 ===")


if __name__ == "__main__":
    main()
