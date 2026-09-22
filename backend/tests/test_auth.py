import jwt
import pytest
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import AuthUser, get_current_user, require_role
from app.core.config import settings


def test_auth_dev_fallback_when_disabled():
    user = get_current_user(credentials=None)
    assert user is not None
    assert user.role == "recruiter"
    assert "recruiter" in user.email


def test_auth_valid_jwt_with_secret(monkeypatch):
    secret = "super-secret-jwt-key-for-tests-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)

    token = jwt.encode(
        {
            "sub": "user-uuid-12345",
            "email": "hiring_lead@example.com",
            "app_metadata": {"role": "hiring_manager"},
        },
        secret,
        algorithm="HS256",
    )

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = get_current_user(credentials=creds)
    assert user.id == "user-uuid-12345"
    assert user.email == "hiring_lead@example.com"
    assert user.role == "hiring_manager"


def test_auth_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "correct-secret-key")

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.structure")
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=creds)
    assert exc.value.status_code == 401


def test_require_role_permissions():
    recruiter = AuthUser(id="1", email="recruiter@test.com", role="recruiter")
    admin = AuthUser(id="2", email="admin@test.com", role="admin")

    # Recruiter check passes
    check_recruiter = require_role(["recruiter", "admin"])
    assert check_recruiter(user=recruiter) == recruiter

    # Admin only check fails for recruiter with 403
    check_admin = require_role(["admin"])
    with pytest.raises(HTTPException) as exc:
        check_admin(user=recruiter)
    assert exc.value.status_code == 403

    # Admin check passes for admin
    assert check_admin(user=admin) == admin
