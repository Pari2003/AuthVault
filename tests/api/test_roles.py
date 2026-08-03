import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestListRoles:
    async def test_list_roles(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/roles/", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_roles_forbidden(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/roles/", headers=auth_header(user_token))
        assert resp.status_code == 403


class TestCreateRole:
    async def test_create_role(self, client: AsyncClient, superuser_token):
        resp = await client.post("/api/v1/roles/", json={
            "name": "viewer",
            "description": "Can view resources"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "viewer"

    async def test_create_role_duplicate(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.post("/api/v1/roles/", json={
            "name": "editor",
            "description": "Duplicate"
        }, headers=auth_header(superuser_token))
        assert resp.status_code == 400


class TestGetRole:
    async def test_get_role(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.get(f"/api/v1/roles/{test_role['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "editor"

    async def test_get_role_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/roles/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestDeleteRole:
    async def test_delete_role(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.delete(f"/api/v1/roles/{test_role['id']}", headers=auth_header(superuser_token))
        assert resp.status_code == 204

    async def test_delete_role_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.delete("/api/v1/roles/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404


class TestRolePermissions:
    async def test_add_permission_to_role(self, client: AsyncClient, superuser_token, test_role, test_permission):
        resp = await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        perm_names = [p["name"] for p in resp.json()["permissions"]]
        assert "users:read" in perm_names

    async def test_add_permission_duplicate(self, client: AsyncClient, superuser_token, test_role, test_permission):
        await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        resp = await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 400

    async def test_add_permission_role_not_found(self, client: AsyncClient, superuser_token, test_permission):
        resp = await client.post(
            f"/api/v1/roles/99999/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_add_permission_perm_not_found(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/99999",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_remove_permission_from_role(self, client: AsyncClient, superuser_token, test_role, test_permission):
        await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        resp = await client.delete(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        perm_names = [p["name"] for p in resp.json()["permissions"]]
        assert "users:read" not in perm_names

    async def test_remove_permission_not_assigned(self, client: AsyncClient, superuser_token, test_role, test_permission):
        resp = await client.delete(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 400

    async def test_remove_permission_role_not_found(self, client: AsyncClient, superuser_token, test_permission):
        resp = await client.delete(
            f"/api/v1/roles/99999/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_remove_permission_perm_not_found(self, client: AsyncClient, superuser_token, test_role):
        resp = await client.delete(
            f"/api/v1/roles/{test_role['id']}/permissions/99999",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404

    async def test_list_role_permissions(self, client: AsyncClient, superuser_token, test_role, test_permission):
        await client.post(
            f"/api/v1/roles/{test_role['id']}/permissions/{test_permission['id']}",
            headers=auth_header(superuser_token)
        )
        resp = await client.get(
            f"/api/v1/roles/{test_role['id']}/permissions",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_list_role_permissions_role_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.get(
            "/api/v1/roles/99999/permissions",
            headers=auth_header(superuser_token)
        )
        assert resp.status_code == 404
