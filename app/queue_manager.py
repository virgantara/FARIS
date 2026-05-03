import asyncio
import json
import time
import uuid
from typing import Any, Dict, Optional

import torch
import redis.asyncio as redis

from app.config import (
    REDIS_URL,
    DEFAULT_MAX_NEW_TOKENS,
    MAX_QUEUE_SIZE,
    JOB_TTL_SECONDS,
)
from app.services.audio_service import download_audio, remove_temp_file
from app.services.qwen_service import qwen_audio_service


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

QUEUE_KEY = "faris:queue:evaluation"
JOB_KEY_PREFIX = "faris:job:"


def job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


async def get_queue_size() -> int:
    return await redis_client.llen(QUEUE_KEY)


async def save_job(job: Dict[str, Any]) -> None:
    await redis_client.set(
        job_key(job["job_id"]),
        json.dumps(job),
        ex=JOB_TTL_SECONDS
    )


async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    raw = await redis_client.get(job_key(job_id))

    if raw is None:
        return None

    return json.loads(raw)


async def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    job = await get_job(job_id)

    if job is None:
        return None

    job.update(updates)
    await save_job(job)

    return job


async def create_job(audio_url: str, max_new_tokens: Optional[int] = None) -> str:
    queue_size = await get_queue_size()

    if queue_size >= MAX_QUEUE_SIZE:
        raise RuntimeError("Queue is full. Please try again later.")

    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "audio_url": audio_url,
        "max_new_tokens": max_new_tokens or DEFAULT_MAX_NEW_TOKENS,
        "status": "queued",
        "result": None,
        "error": None,
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
    }

    await save_job(job)
    await redis_client.rpush(QUEUE_KEY, job_id)

    return job_id


async def inference_worker(worker_id: int):
    print(f"Redis inference worker {worker_id} started.")

    while True:
        temp_audio_path = None

        try:
            item = await redis_client.blpop(QUEUE_KEY, timeout=5)

            if item is None:
                await asyncio.sleep(0.1)
                continue

            _, job_id = item

            job = await get_job(job_id)

            if job is None:
                continue

            print(f"[Worker {worker_id}] Processing job: {job_id}")

            await update_job(
                job_id,
                {
                    "status": "processing",
                    "started_at": time.time(),
                    "error": None,
                }
            )

            temp_audio_path = await asyncio.to_thread(
                download_audio,
                job["audio_url"]
            )

            result = await asyncio.to_thread(
                qwen_audio_service.evaluate_audio,
                temp_audio_path,
                job["audio_url"],
                int(job["max_new_tokens"])
            )

            await update_job(
                job_id,
                {
                    "status": "completed",
                    "result": result,
                    "finished_at": time.time(),
                }
            )

            print(f"[Worker {worker_id}] Completed job: {job_id}")

        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()

            if "job_id" in locals():
                await update_job(
                    job_id,
                    {
                        "status": "failed",
                        "error": "CUDA out of memory. Try shorter audio or reduce max_new_tokens.",
                        "finished_at": time.time(),
                    }
                )

            print(f"[Worker {worker_id}] CUDA out of memory.")

        except Exception as e:
            if "job_id" in locals():
                await update_job(
                    job_id,
                    {
                        "status": "failed",
                        "error": str(e),
                        "finished_at": time.time(),
                    }
                )

            print(f"[Worker {worker_id}] Failed: {str(e)}")

        finally:
            remove_temp_file(temp_audio_path)