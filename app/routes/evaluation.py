from fastapi import APIRouter, HTTPException

# from app.auth import verify_api_key
from app.config import MODEL_NAME
from app.schemas import (
    AudioUrlRequest,
    JobSubmitResponse,
    JobStatusResponse,
    JobResultResponse,
)
from app.queue_manager import (
    create_job,
    get_job,
    get_queue_size,
)



router = APIRouter(
    tags=["Evaluation"],
    # dependencies=[Depends(verify_api_key)]
)


@router.get("/")
async def root():
    queue_size = await get_queue_size()

    return {
        "message": "FARIS Speaking Evaluation API is running",
        "model": MODEL_NAME,
        "queue_size": queue_size,
    }


@router.post("/evaluate-url", response_model=JobSubmitResponse)
async def submit_audio_url(request: AudioUrlRequest):
    try:
        job_id = await create_job(
            audio_url=request.audio_url,
            max_new_tokens=request.max_new_tokens
        )

        queue_size = await get_queue_size()

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Job submitted successfully. Use /jobs/{job_id} to check status.",
            "queue_size": queue_size,
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
async def check_job_status(job_id: str):
    job = await get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired."
        )

    queue_size = await get_queue_size()

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "queue_size": queue_size,
        "error": job["error"],
    }


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    job = await get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired."
        )

    if job["status"] != "completed":
        return {
            "success": job["status"] != "failed",
            "job_id": job_id,
            "status": job["status"],
            "result": None,
            "error": job["error"],
        }

    return {
        "success": True,
        "job_id": job_id,
        "status": "completed",
        "result": job["result"],
        "error": None,
    }