import asyncio

from fastapi import FastAPI

from app.config import INFERENCE_WORKERS
from app.routes.evaluation import router as evaluation_router
from app.queue_manager import inference_worker


app = FastAPI(
    title="FARIS Speaking Evaluation API",
    description="Audio URL -> queue -> Qwen2-Audio-7B-Instruct -> FARIS evaluation",
    version="1.0.0"
)

app.include_router(evaluation_router)


@app.on_event("startup")
async def startup_event():
    for worker_id in range(INFERENCE_WORKERS):
        asyncio.create_task(inference_worker(worker_id + 1))