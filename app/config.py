import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

DEFAULT_MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "700"))

MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "20"))
INFERENCE_WORKERS = int(os.getenv("INFERENCE_WORKERS", "1"))

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "Qwen/Qwen2-Audio-7B-Instruct"
)