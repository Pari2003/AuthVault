import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.role import Role, Permission, role_permission_association
from app.models.audit import AuditLog

TEST_DB_URL = "sqlite+aiosqlite://"

engine_test = create_async_engine(TEST_DB_URL, echo=False)
async_session_test = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)

# We use a single connection with a nested transaction so that the
# db_session fixture and the app's `get_db` dependency share the
# same in-flight transaction/data.

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a DB session that shares the same engine as the app override."""
    async with async_session_test() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user via the API and return user data + raw password."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert resp.status_code == 201
    data = resp.json()
    data["_password"] = "testpassword123"
    return data


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser directly in the DB (can't self-escalate via API)."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_role(client: AsyncClient, superuser_token: str) -> dict:
    """Create a test role via the API."""
    resp = await client.post("/api/v1/roles/", json={
        "name": "editor",
        "description": "Can edit content"
    }, headers=auth_header(superuser_token))
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def test_permission(client: AsyncClient, superuser_token: str) -> dict:
    """Create a test permission via the API."""
    resp = await client.post("/api/v1/permissions/", json={
        "name": "users:read",
        "description": "Can read users"
    }, headers=auth_header(superuser_token))
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def user_token(test_user: dict, client: AsyncClient) -> str:
    """Login as the test user and return the token."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": test_user["email"],
        "password": test_user["_password"]
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def superuser_token(superuser: User, client: AsyncClient) -> str:
    """Login as the superuser and return the token."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com",
        "password": "adminpassword123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
