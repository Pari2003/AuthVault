import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AuthVault"

    async def test_metrics(self, client: AsyncClient):
        resp = await client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "AuthVault"
        assert data["uptime_check"] is True
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
