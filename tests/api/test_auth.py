import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestAuthRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "strongpassword123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "anotherpassword"
        })
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]


class TestAuthLogin:
    async def test_login_success(self, client: AsyncClient, test_user):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "noone@example.com",
            "password": "whatever"
        })
        assert resp.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, superuser_token):
        # Register a user, then deactivate them via superuser, then try to login
        reg = await client.post("/api/v1/auth/register", json={
            "email": "inactive@example.com",
            "password": "password123"
        })
        user_id = reg.json()["id"]
        await client.post(
            f"/api/v1/users/{user_id}/deactivate",
            headers=auth_header(superuser_token)
        )
        resp = await client.post("/api/v1/auth/login", data={
            "username": "inactive@example.com",
            "password": "password123"
        })
        assert resp.status_code == 400


class TestAuthMe:
    async def test_get_me(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/auth/me", headers=auth_header(user_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    async def test_get_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestTokenRefresh:
    async def test_refresh_token(self, client: AsyncClient, user_token):
        resp = await client.post("/api/v1/auth/token/refresh", headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestTokenValidation:
    async def test_validate_valid_token(self, client: AsyncClient, user_token, test_user):
        resp = await client.post("/api/v1/auth/validate-token", headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["user_id"] == test_user["id"]

    async def test_validate_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/validate-token", headers=auth_header("invalidtoken"))
        assert resp.status_code == 401


class TestPasswordChange:
    async def test_change_password_success(self, client: AsyncClient, user_token):
        resp = await client.post(
            "/api/v1/auth/password/change",
            params={"current_password": "testpassword123", "new_password": "newpassword456"},
            headers=auth_header(user_token)
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password changed successfully"

    async def test_change_password_wrong_current(self, client: AsyncClient, user_token):
        resp = await client.post(
            "/api/v1/auth/password/change",
            params={"current_password": "wrongcurrent", "new_password": "newpassword456"},
            headers=auth_header(user_token)
        )
        assert resp.status_code == 400


class TestInvalidTokenPayload:
    async def test_token_with_no_sub(self, client: AsyncClient):
        from jose import jwt
        from app.core.config import get_settings
        settings = get_settings()
        token = jwt.encode({"exp": 9999999999}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 401

    async def test_token_with_nonexistent_user(self, client: AsyncClient):
        from app.core.security import create_access_token
        token = create_access_token(subject=99999)
        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 401
