import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_user import create_user, get_user, get_user_by_email, get_users, update_user, delete_user
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import verify_password

pytestmark = pytest.mark.asyncio


class TestCrudUser:
    async def test_create_and_get_user(self, db_session: AsyncSession):
        user_in = UserCreate(email="crud@example.com", password="password123")
        user = await create_user(db_session, user_in)
        assert user.email == "crud@example.com"
        assert user.id is not None

        fetched = await get_user(db_session, user.id)
        assert fetched is not None
        assert fetched.email == "crud@example.com"

    async def test_get_user_by_email(self, db_session: AsyncSession):
        user_in = UserCreate(email="byemail@example.com", password="password123")
        await create_user(db_session, user_in)
        
        fetched = await get_user_by_email(db_session, "byemail@example.com")
        assert fetched is not None
        assert fetched.email == "byemail@example.com"

    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        fetched = await get_user_by_email(db_session, "nonexistent@example.com")
        assert fetched is None

    async def test_get_users(self, db_session: AsyncSession):
        await create_user(db_session, UserCreate(email="u1@example.com", password="p"))
        await create_user(db_session, UserCreate(email="u2@example.com", password="p"))
        users = await get_users(db_session)
        assert len(users) >= 2

    async def test_update_user(self, db_session: AsyncSession):
        user = await create_user(db_session, UserCreate(email="toupdate@example.com", password="p"))
        updated = await update_user(db_session, user.id, UserUpdate(email="updated@example.com"))
        assert updated.email == "updated@example.com"

    async def test_update_user_password(self, db_session: AsyncSession):
        user = await create_user(db_session, UserCreate(email="pwupdate@example.com", password="old"))
        updated = await update_user(db_session, user.id, UserUpdate(password="newpassword"))
        assert verify_password("newpassword", updated.hashed_password)

    async def test_update_user_not_found(self, db_session: AsyncSession):
        result = await update_user(db_session, 99999, UserUpdate(email="x@x.com"))
        assert result is None

    async def test_delete_user(self, db_session: AsyncSession):
        user = await create_user(db_session, UserCreate(email="todelete@example.com", password="p"))
        success = await delete_user(db_session, user.id)
        assert success is True
        assert await get_user(db_session, user.id) is None

    async def test_delete_user_not_found(self, db_session: AsyncSession):
        success = await delete_user(db_session, 99999)
        assert success is False

    async def test_get_user_not_found(self, db_session: AsyncSession):
        fetched = await get_user(db_session, 99999)
        assert fetched is None
