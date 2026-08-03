import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_role import (
    create_role, get_role, get_role_by_name, get_roles, delete_role,
    create_permission, get_permission, get_permissions, delete_permission
)
from app.schemas.role import RoleCreate, PermissionCreate

pytestmark = pytest.mark.asyncio


class TestCrudRole:
    async def test_create_and_get_role(self, db_session: AsyncSession):
        role_in = RoleCreate(name="test_role", description="Test role")
        role = await create_role(db_session, role_in)
        assert role.name == "test_role"

        fetched = await get_role(db_session, role.id)
        assert fetched is not None
        assert fetched.name == "test_role"

    async def test_get_role_by_name(self, db_session: AsyncSession):
        await create_role(db_session, RoleCreate(name="named_role"))
        fetched = await get_role_by_name(db_session, "named_role")
        assert fetched is not None

    async def test_get_roles(self, db_session: AsyncSession):
        await create_role(db_session, RoleCreate(name="r1"))
        await create_role(db_session, RoleCreate(name="r2"))
        roles = await get_roles(db_session)
        assert len(roles) >= 2

    async def test_delete_role(self, db_session: AsyncSession):
        role = await create_role(db_session, RoleCreate(name="to_delete"))
        success = await delete_role(db_session, role.id)
        assert success is True

    async def test_delete_role_not_found(self, db_session: AsyncSession):
        success = await delete_role(db_session, 99999)
        assert success is False


class TestCrudPermission:
    async def test_create_and_get_permission(self, db_session: AsyncSession):
        perm_in = PermissionCreate(name="test:perm", description="Test")
        perm = await create_permission(db_session, perm_in)
        assert perm.name == "test:perm"

        fetched = await get_permission(db_session, perm.id)
        assert fetched is not None

    async def test_get_permissions(self, db_session: AsyncSession):
        await create_permission(db_session, PermissionCreate(name="p1"))
        await create_permission(db_session, PermissionCreate(name="p2"))
        perms = await get_permissions(db_session)
        assert len(perms) >= 2

    async def test_delete_permission(self, db_session: AsyncSession):
        perm = await create_permission(db_session, PermissionCreate(name="to_del"))
        success = await delete_permission(db_session, perm.id)
        assert success is True

    async def test_delete_permission_not_found(self, db_session: AsyncSession):
        success = await delete_permission(db_session, 99999)
        assert success is False
