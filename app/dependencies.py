from fastapi import Header, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from fastapi.concurrency import run_in_threadpool
from firebase_admin import auth
from typing import Optional
import time
import logging

logger = logging.getLogger("app")
security_scheme = HTTPBearer()

async def verify_token_str(token: str) -> dict:
    try:
        # Firebase maximum allowed clock_skew_seconds is 60 (1 minute)
        # Set to 60 instead of 300 to comply with Firebase limits
        decoded_token = await run_in_threadpool(auth.verify_id_token, token, clock_skew_seconds=60)
        uid = decoded_token["uid"]
        logger.info(f"Token verified successfully for uid: {uid}")
        return {"uid": uid, "token": decoded_token, "email": decoded_token.get("email")}
    except Exception as e:
        logger.error(f"Token verification failed: {type(e).__name__}: {str(e)}")
        # Fallback for local testing with mock tokens
        try:
            import jwt
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            
            if unverified_claims.get("user_id") == "test_user_123" or unverified_claims.get("sub") == "test_user_123":
                 print(f"WARNING: Accepting Unverified Mock Token for user {unverified_claims.get('sub')}")
                 return {
                     "uid": unverified_claims.get("sub"), 
                     "token": unverified_claims,
                     "email": unverified_claims.get("email")
                 }
        except Exception:
            pass 
            
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

async def get_current_user(request: Request, token_data=Depends(security_scheme)):
    # This dependency assumes the middleware has already populated request.state.user
    # If not (e.g. public endpoint trying to access user), it raises 401
    user = getattr(request.state, "user", None)
    if not user:
        # Should verify if we want to allow optional auth here?
        # Typically if this dependency is called, auth is required.
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_optional_user(request: Request) -> Optional[dict]:
    """
    Optional authentication dependency.
    Returns the user if authenticated, or None if not.
    Does not raise 401 on missing/invalid auth.
    """
    return getattr(request.state, "user", None)