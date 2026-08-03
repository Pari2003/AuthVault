import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestRBACWithPermissions:
    """Test that RBAC permission checks work correctly end-to-end."""

    async def test_user_with_role_permission_can_access(
        self, client: AsyncClient, superuser_token, test_user, user_token
    ):
        """A user with the right role/permission can access protected resources."""
        # Create a role with users:read permission via API
        role_resp = await client.post("/api/v1/roles/", json={
            "name": "reader",
            "description": "Can read"
        }, headers=auth_header(superuser_token))
        role_id = role_resp.json()["id"]

        perm_resp = await client.post("/api/v1/permissions/", json={
            "name": "users:read",
            "description": "Read users"
        }, headers=auth_header(superuser_token))
        perm_id = perm_resp.json()["id"]

        # Assign permission to role
        await client.post(
            f"/api/v1/roles/{role_id}/permissions/{perm_id}",
            headers=auth_header(superuser_token)
        )

        # Assign role to user
        await client.post(
            f"/api/v1/users/{test_user['id']}/role/{role_id}",
            headers=auth_header(superuser_token)
        )

        # Now user should be able to list users
        resp = await client.get("/api/v1/users/", headers=auth_header(user_token))
        assert resp.status_code == 200

    async def test_user_without_permission_denied(
        self, client: AsyncClient, user_token
    ):
        """A user without the required permission gets 403."""
        resp = await client.get("/api/v1/users/", headers=auth_header(user_token))
        assert resp.status_code == 403

    async def test_user_with_role_but_wrong_permission(
        self, client: AsyncClient, superuser_token, test_user, user_token
    ):
        """A user with a role that lacks the needed permission still gets 403."""
        role_resp = await client.post("/api/v1/roles/", json={
            "name": "limited",
            "description": "Limited access"
        }, headers=auth_header(superuser_token))
        role_id = role_resp.json()["id"]

        perm_resp = await client.post("/api/v1/permissions/", json={
            "name": "reports:read",
            "description": "Read reports"
        }, headers=auth_header(superuser_token))
        perm_id = perm_resp.json()["id"]

        await client.post(
            f"/api/v1/roles/{role_id}/permissions/{perm_id}",
            headers=auth_header(superuser_token)
        )

        await client.post(
            f"/api/v1/users/{test_user['id']}/role/{role_id}",
            headers=auth_header(superuser_token)
        )

        # Should still be forbidden for users:delete
        resp = await client.delete(f"/api/v1/users/{test_user['id']}", headers=auth_header(user_token))
        assert resp.status_code == 403
