from app.game.dealer import DealerReferee
from app.ai.engine_smart import SmartAIEngine   # ← 替换此处
# from app.ai.engine_rule import RuleBasedAIEngine  # 旧的，不再使用


# 实例化裁判
dealer = DealerReferee()

# 使用智能 AI（方案 A）
ai_engine = SmartAIEngine()   # ← 使用新的智能 AI
