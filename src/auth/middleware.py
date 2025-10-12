from fastapi import Request, HTTPException
from src.cache.session_manager import session_manager
from src.database.databases import Database
from src.auth.authentication import AuthenticationService


def get_current_user(request: Request):
    """Middleware to get current user from session"""
    session_token = request.headers.get("Authorization")

    if not session_token or not session_token.startswith("Bearer "):
        return None

    session_token = session_token.replace("Bearer ", "")

    with Database.get_session() as db:
        auth_service = AuthenticationService(db)
        user = auth_service.get_current_user(session_token)
        return user


def auth_required(request: Request):
    """Middleware that requires authentication"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
