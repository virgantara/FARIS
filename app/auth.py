from fastapi import Header, HTTPException, status

from app.config import API_KEY


async def verify_api_key(x_api_key: str | None = Header(default=None)):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY is not configured on the server."
        )

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )

    return True