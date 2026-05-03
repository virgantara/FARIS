import uvicorn
from app import APP_HOST, APP_PORT

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False
    )