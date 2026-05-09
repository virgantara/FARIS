import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import INFERENCE_WORKERS
from app.routes.evaluation import router as evaluation_router
from app.queue_manager import inference_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FARIS Speaking Evaluation API...")

    tasks = []

    for worker_id in range(INFERENCE_WORKERS):
        task = asyncio.create_task(
            inference_worker(worker_id + 1)
        )
        tasks.append(task)

    print(f"{INFERENCE_WORKERS} inference worker(s) started.")

    yield

    print("Shutting down FARIS Speaking Evaluation API...")

    for task in tasks:
        task.cancel()


app = FastAPI(
    title="FARIS Speaking Evaluation API",
    description="Audio URL -> Redis Queue -> Qwen3.5 Omni Flash -> FARIS evaluation",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(evaluation_router)