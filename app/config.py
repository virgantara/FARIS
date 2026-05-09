import os
from dotenv import load_dotenv

load_dotenv()


# =========================
# App Config
# =========================
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))


# =========================
# Model Config
# =========================
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "qwen3.5-omni-flash"
)

DEFAULT_MAX_NEW_TOKENS = int(
    os.getenv("MAX_NEW_TOKENS", "1800")
)


# =========================
# DashScope / Qwen API Config
# =========================
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)


# =========================
# Redis Queue Config
# =========================
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

MAX_QUEUE_SIZE = int(
    os.getenv("MAX_QUEUE_SIZE", "20")
)

INFERENCE_WORKERS = int(
    os.getenv("INFERENCE_WORKERS", "1")
)

JOB_TTL_SECONDS = int(
    os.getenv("JOB_TTL_SECONDS", "3600")
)