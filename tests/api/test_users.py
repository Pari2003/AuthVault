import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestListUsers:
    async def test_list_users_as_superuser(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/users/", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_users_forbidden_for_regular_user(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/users/", headers=auth_header(user_token))
        assert resp.status_code == 403

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/")
        assert resp.status_code == 401


class TestCreateUser:
    async def test_create_user_as_superuser(self, client: AsyncClient, superuser_token):
        resp = await client.post("/api/v1/users/", json={
            "email": "created@example.com",
            "password": "password123"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 201
        assert resp.json()["email"] == "created@example.com"

    async def test_create_user_duplicate_email(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.post("/api/v1/users/", json={
            "email": "test@example.com",
            "password": "password123"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 400

    async def test_create_user_forbidden(self, client: AsyncClient, user_token):
        resp = await client.post("/api/v1/users/", json={
            "email": "new@example.com",
            "password": "password123"
        }, headers=auth_header(user_token))
        assert resp.status_code == 403


class TestReadUser:
    async def test_get_user_by_id(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.get(f"/api/v1/users/{test_user['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    async def test_get_user_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/users/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestUpdateUser:
    async def test_update_user(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.put(f"/api/v1/users/{test_user['id']}", json={
            "email": "updated@example.com"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@example.com"

    async def test_update_user_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.put("/api/v1/users/99999", json={
            "email": "ghost@example.com"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestDeleteUser:
    async def test_delete_user(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.delete(f"/api/v1/users/{test_user['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 204

    async def test_delete_user_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.delete("/api/v1/users/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestUserMe:
    async def test_get_me(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/users/me", headers=auth_header(user_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    async def test_update_me(self, client: AsyncClient, user_token):
        resp = await client.put("/api/v1/users/me", json={
            "email": "mynewemail@example.com"
        }, headers=auth_header(user_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "mynewemail@example.com"


class TestRoleAssignment:
    async def test_assign_role(self, client: AsyncClient, superuser_token, test_user, test_role):
        resp = await client.post(
            f"/api/v1/users/{test_user['id']}/role/{test_role['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        assert resp.json()["role_id"] == test_role["id"]

    async def test_assign_role_not_found_role(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.post(
            f"/api/v1/users/{test_user['id']}/role/99999",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_assign_role_not_found_user(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.post(
            f"/api/v1/users/99999/role/{test_role['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_remove_role(self, client: AsyncClient, superuser_token, test_user, test_role):
        await client.post(
            f"/api/v1/users/{test_user['id']}/role/{test_role['id']}",
            headers=auth_header(superuser_token)
        )
        resp = await client.delete(
            f"/api/v1/users/{test_user['id']}/role",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        assert resp.json()["role_id"] is None

    async def test_remove_role_user_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.delete(
            "/api/v1/users/99999/role",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404


class TestActivateDeactivate:
    async def test_activate_user(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.post(
            f"/api/v1/users/{test_user['id']}/activate",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_deactivate_user(self, client: AsyncClient, superuser_token, test_user):
        resp = await client.post(
            f"/api/v1/users/{test_user['id']}/deactivate",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_activate_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.post("/api/v1/users/99999/activate", headers=auth_header(superuser_token))
        assert resp.status_code == 404

    async def test_deactivate_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.post("/api/v1/users/99999/deactivate", headers=auth_header(superuser_token))
        assert resp.status_code == 404

    async def test_activate_forbidden(self, client: AsyncClient, user_token, test_user):
        resp = await client.post(
            f"/api/v1/users/{test_user['id']}/activate",
            headers=auth_header(user_token)
        )
        assert resp.status_code == 403
