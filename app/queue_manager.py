import asyncio
import uuid
import time
import torch

from typing import Dict, Any

from app.config import DEFAULT_MAX_NEW_TOKENS, MAX_QUEUE_SIZE
from app.services.audio_service import download_audio, remove_temp_file
from app.services.qwen_service import qwen_audio_service


job_queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
jobs: Dict[str, Dict[str, Any]] = {}


def create_job(audio_url: str, max_new_tokens: int | None = None) -> str:
    if job_queue.full():
        raise RuntimeError("Queue is full. Please try again later.")

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
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

    job_queue.put_nowait(job_id)

    return job_id


def get_job(job_id: str) -> Dict[str, Any] | None:
    return jobs.get(job_id)


def get_queue_size() -> int:
    return job_queue.qsize()


async def inference_worker(worker_id: int):
    print(f"Inference worker {worker_id} started.")

    while True:
        job_id = await job_queue.get()
        job = jobs.get(job_id)

        if job is None:
            job_queue.task_done()
            continue

        temp_audio_path = None

        try:
            print(f"[Worker {worker_id}] Processing job: {job_id}")

            job["status"] = "processing"
            job["started_at"] = time.time()

            temp_audio_path = download_audio(job["audio_url"])

            result = await asyncio.to_thread(
                qwen_audio_service.evaluate_audio,
                temp_audio_path,
                job["audio_url"],
                job["max_new_tokens"]
            )

            job["result"] = result
            job["status"] = "completed"
            job["finished_at"] = time.time()

            print(f"[Worker {worker_id}] Completed job: {job_id}")

        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()

            job["status"] = "failed"
            job["error"] = "CUDA out of memory. Try shorter audio or reduce max_new_tokens."
            job["finished_at"] = time.time()

            print(f"[Worker {worker_id}] CUDA OOM job: {job_id}")

        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            job["finished_at"] = time.time()

            print(f"[Worker {worker_id}] Failed job {job_id}: {str(e)}")

        finally:
            remove_temp_file(temp_audio_path)
            job_queue.task_done()