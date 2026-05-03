from fastapi import APIRouter, HTTPException

from app.config import MODEL_NAME
from app.schemas import (
    AudioUrlRequest,
    JobSubmitResponse,
    JobStatusResponse,
    JobResultResponse
)
from app.queue_manager import (
    create_job,
    get_job,
    get_queue_size
)


router = APIRouter(tags=["Evaluation"])


@router.get("/")
def root():
    return {
        "message": "FARIS Speaking Evaluation API is running",
        "model": MODEL_NAME,
        "queue_size": get_queue_size()
    }


@router.post("/evaluate-url", response_model=JobSubmitResponse)
def submit_audio_url(request: AudioUrlRequest):
    try:
        job_id = create_job(
            audio_url=request.audio_url,
            max_new_tokens=request.max_new_tokens
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Job submitted successfully. Use /jobs/{job_id} to check status.",
            "queue_size": get_queue_size()
        }

    except RuntimeError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def check_job_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "queue_size": get_queue_size(),
        "error": job["error"]
    }


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
def get_job_result(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if job["status"] == "queued":
        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "result": None,
            "error": None
        }

    if job["status"] == "processing":
        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "result": None,
            "error": None
        }

    if job["status"] == "failed":
        return {
            "success": False,
            "job_id": job_id,
            "status": "failed",
            "result": None,
            "error": job["error"]
        }

    return {
        "success": True,
        "job_id": job_id,
        "status": "completed",
        "result": job["result"],
        "error": None
    }