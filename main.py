
from app.main import app  # Expose FastAPI app for ASGI servers
import uvicorn
import os

if __name__ == "__main__":
    # When running locally for development, use $PORT if provided so local invocation can mimic the
    # production environment (Railway sets $PORT). Default to 8000 for local dev.
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
