from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routes import user, events, workshops, webhooks
from app.dependencies import verify_token_str
import logging

# Basic logger used for simple request/health-check visibility in logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="TALOS Backend", version="1.0.0")

# CORS
origins = [
    "http://localhost:3000",
    "https://talos-nine.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Authorization Middleware ---
def is_public_endpoint(request: Request) -> bool:
    path = request.url.path
    method = request.method.upper()

    # Treat HEAD like GET so health checks using HEAD succeed
    if method == "HEAD":
        method = "GET"

    # 1. Root & Docs
    if path in ["/", "/docs", "/redoc", "/openapi.json"]:
        return True
    
    # 2. Webhooks (Signature verified internally)
    if path.startswith("/api/webhooks"):
        return True
    
    # 3. Events (GET is public)
    if path.startswith("/api/events") and method == "GET":
        return True

    # 4. Workshops (GET is public)
    if path.startswith("/api/workshops") and method == "GET":
        return True
        
    # 5. OPTIONS (CORS preflight)
    if method == "OPTIONS":
        return True

    return False

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
        
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    if is_public_endpoint(request):
        # Even for public endpoints, if a token IS provided, we might want to resolve it 
        # (optional auth). But for now, let's keep it simple: Public = No Auth Check.
        response = await call_next(request)
        return response

    # Protected Endpoint
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid authentication token"})
    
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
    else:
        token = auth_header
        
    try:
        user = await verify_token_str(token)
        request.state.user = user
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": f"Authentication failed: {str(e)}"})
        
    response = await call_next(request)
    return response

# Routes
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(workshops.router, prefix="/api/workshops", tags=["Workshops"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to TALOS Backend API"}


@app.get("/healthz")
async def healthz():
    # Simple health endpoint for platform health checks
    return {"status": "ok"}