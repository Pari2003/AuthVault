import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestListPermissions:
    async def test_list_permissions(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/permissions/", headers=auth_header(superuser_token))
        assert resp.status_code == 200

    async def test_list_permissions_forbidden(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/permissions/", headers=auth_header(user_token))
        assert resp.status_code == 403


class TestCreatePermission:
    async def test_create_permission(self, client: AsyncClient, superuser_token):
        resp = await client.post("/api/v1/permissions/", json={
            "name": "users:write",
            "description": "Can write users"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "users:write"

    async def test_create_permission_duplicate(self, client: AsyncClient, superuser_token, test_permission):
        resp = await client.post("/api/v1/permissions/", json={
            "name": "users:read",
            "description": "Duplicate"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 400


class TestGetPermission:
    async def test_get_permission(self, client: AsyncClient, superuser_token, test_permission):
        resp = await client.get(f"/api/v1/permissions/{test_permission['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "users:read"

    async def test_get_permission_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/permissions/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestDeletePermission:
    async def test_delete_permission(self, client: AsyncClient, superuser_token, test_permission):
        resp = await client.delete(f"/api/v1/permissions/{test_permission['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 204

    async def test_delete_permission_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.delete("/api/v1/permissions/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404
