import pytest
from httpx import AsyncClient
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestAuditLogs:
    async def test_list_audit_logs_superuser(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/audit/", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_audit_logs_forbidden(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/audit/", headers=auth_header(user_token))
        assert resp.status_code == 403

    async def test_get_my_audit_logs(self, client: AsyncClient, user_token):
        resp = await client.get("/api/v1/audit/me", headers=auth_header(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_audit_log_by_id_not_found(self, client: AsyncClient, superuser_token):
        resp = await client.get("/api/v1/audit/99999", headers=auth_header(superuser_token))
        assert resp.status_code == 404

    async def test_get_audit_log_by_id(self, client: AsyncClient, superuser_token):
        # Login generates audit logs, so list them and fetch the first one
        logs_resp = await client.get("/api/v1/audit/", headers=auth_header(superuser_token))
        logs = logs_resp.json()
        assert len(logs) > 0
        log_id = logs[0]["id"]

        resp = await client.get(f"/api/v1/audit/{log_id}", headers=auth_header(superuser_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == log_id
