from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Optional, List

from app.models.role import Role, Permission
from app.schemas.role import RoleCreate, PermissionCreate

async def get_role(db: AsyncSession, role_id: int) -> Optional[Role]:
    result = await db.execute(select(Role).filter(Role.id == role_id))
    return result.scalars().first()

async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
    result = await db.execute(select(Role).filter(Role.name == name))
    return result.scalars().first()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
    result = await db.execute(select(Role).offset(skip).limit(limit))
    return result.scalars().all()

async def create_role(db: AsyncSession, role: RoleCreate) -> Role:
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def delete_role(db: AsyncSession, role_id: int) -> bool:
    result = await db.execute(delete(Role).where(Role.id == role_id))
    await db.commit()
    return result.rowcount > 0

async def get_permission(db: AsyncSession, permission_id: int) -> Optional[Permission]:
    result = await db.execute(select(Permission).filter(Permission.id == permission_id))
    return result.scalars().first()

async def get_permissions(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Permission]:
    result = await db.execute(select(Permission).offset(skip).limit(limit))
    return result.scalars().all()

async def create_permission(db: AsyncSession, permission: PermissionCreate) -> Permission:
    db_perm = Permission(name=permission.name, description=permission.description)
    db.add(db_perm)
    await db.commit()
    await db.refresh(db_perm)
    return db_perm

async def delete_permission(db: AsyncSession, permission_id: int) -> bool:
    result = await db.execute(delete(Permission).where(Permission.id == permission_id))
    await db.commit()
    return result.rowcount > 0
