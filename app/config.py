from pathlib import Path

# 项目根目录（backend 目录）
BASE_DIR = Path(__file__).resolve().parent.parent

# 日志目录
LOG_DIR = BASE_DIR.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 数据目录
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 管理员访问 token（控制面板用）
ADMIN_TOKEN = "admin"

# 后端监听设置（真正端口由 run_dev.bat 决定）
HOST = "127.0.0.1"
PORT = 8080

# AI 设备：'cpu' 或 'cuda'（后续可扩展）
AI_DEVICE = "cpu"
