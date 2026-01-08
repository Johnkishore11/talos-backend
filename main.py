
from app.main import app  # Expose FastAPI app for ASGI servers
import uvicorn

if __name__ == "__main__":
    # When running locally for development, reload is convenient. In production (Railway), the platform
    # will import the module and look for `app` directly (so exposing `app` above is required).
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
