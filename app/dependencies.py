from fastapi import Header, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from firebase_admin import auth
from typing import Optional

security_scheme = HTTPBearer()

async def verify_token_str(token: str) -> dict:
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        return {"uid": uid, "token": decoded_token, "email": decoded_token.get("email")}
    except Exception as e:
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