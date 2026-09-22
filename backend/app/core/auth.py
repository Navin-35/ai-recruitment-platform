from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.supabase import get_supabase_client

security = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    id: str
    email: Optional[str] = None
    role: str = "recruiter"
    aud: str = "authenticated"


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthUser:
    """
    Validates Supabase JWT tokens and extracts user identity and RBAC role.
    If auth enforcement is disabled and no token is passed, falls back to a development recruiter.
    """
    if not credentials:
        if settings.enable_auth_enforcement:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Missing Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Development / test fallback user
        return AuthUser(
            id="00000000-0000-0000-0000-000000000001",
            email="recruiter@recruitment-platform.local",
            role="recruiter",
        )

    token = credentials.credentials

    # 1. Attempt verification via Supabase JWT secret (fastest local check)
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            user_id = payload.get("sub", "")
            email = payload.get("email")
            role = payload.get("app_metadata", {}).get("role") or payload.get("role", "recruiter")
            return AuthUser(id=user_id, email=email, role=role)
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid JWT token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Attempt verification via Supabase Auth API
    supabase = get_supabase_client()
    if supabase:
        try:
            user_res = supabase.auth.get_user(token)
            if user_res and user_res.user:
                u = user_res.user
                role = (u.app_metadata or {}).get("role", "recruiter")
                return AuthUser(id=str(u.id), email=u.email, role=role)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supabase auth validation failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 3. Permissive decode when no secret configured (development inspection)
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        user_id = unverified_payload.get("sub", "dev-user")
        email = unverified_payload.get("email", "dev@example.com")
        role = unverified_payload.get("app_metadata", {}).get("role") or unverified_payload.get("role", "recruiter")
        return AuthUser(id=user_id, email=email, role=role)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(allowed_roles: list[str]):
    """
    Dependency factory to enforce role-based access control (RBAC).
    Allowed roles e.g.: ['admin', 'recruiter', 'hiring_manager']
    """
    def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{user.role}'. Required one of: {allowed_roles}",
            )
        return user

    return role_checker
