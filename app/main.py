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

app = FastAPI(
    title="TALOS Backend",
    version="1.0.0",
    redirect_slashes=False  # 🔥 CRITICAL FIX
)

# CORS
origins = [
    "http://localhost:3000",
    "https://talos-nine.vercel.app",
    "https://taloscit.in",
    "https://www.taloscit.in"
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
    
    # 3. Events (GET is public, check-registration uses optional auth in route handler)
    if path.startswith("/api/events") and method == "GET":
        return True

    # 4. Workshops (GET is public, check-registration uses optional auth in route handler)
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
    
    is_public = is_public_endpoint(request)
    auth_header = request.headers.get("Authorization")
    logger.info(f"Auth header present: {bool(auth_header)}, length: {len(auth_header) if auth_header else 0}, is_public: {is_public}")
    
    # For public endpoints without auth header, just proceed
    if is_public and not auth_header:
        response = await call_next(request)
        return response
    
    # For protected endpoints, auth is required
    if not is_public and not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid authentication token"})
    
    # If we have an auth header, try to verify it (for both public and protected endpoints)
    if auth_header:
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
        else:
            token = auth_header
        
        logger.info(f"Token length: {len(token)}, first 20 chars: {token[:20] if len(token) > 20 else token}...")
            
        try:
            user = await verify_token_str(token)
            logger.info(f"Token verified successfully for user: {user.get('email')}")
            request.state.user = user
        except HTTPException as e:
            logger.error(f"Token verification failed: {e.detail}")
            if not is_public:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
            # For public endpoints with invalid token, just continue without user
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            if not is_public:
                return JSONResponse(status_code=401, content={"detail": f"Authentication failed: {str(e)}"})
            # For public endpoints with invalid token, just continue without user
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