from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from supabase_client import get_supabase_client

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    supabase: Client


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(credentials.credentials)
        user = user_response.user
        if user is None or not user.id:
            raise ValueError("Supabase returned no authenticated user")
        supabase.postgrest.auth(credentials.credentials)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    return AuthContext(user_id=str(user.id), supabase=supabase)
