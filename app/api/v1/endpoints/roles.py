from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.crud.crud_role import (
    get_role, get_role_by_name, get_roles, create_role, delete_role,
    get_permission
)
from app.crud.crud_audit import log_action
from app.schemas.role import Role as RoleSchema, RoleCreate, Permission as PermissionSchema
from app.schemas.audit import AuditLogCreate
from app.api.deps import get_current_superuser
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[RoleSchema], summary="List all roles")
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a paginated list of all roles."""
    roles = await get_roles(db, skip=skip, limit=limit)
    return roles


@router.post("/", response_model=RoleSchema, status_code=201, summary="Create a new role")
async def create_new_role(
    role_in: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Create a new role. Role name must be unique."""
    existing = await get_role_by_name(db, name=role_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    new_role = await create_role(db, role_in)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="ROLE_CREATED",
        resource=f"roles/{new_role.id}",
        details=f"Role '{new_role.name}' created.",
        ip_address=request.client.host if request.client else None
    ))
    return new_role


@router.get("/{role_id}", response_model=RoleSchema, summary="Get role by ID")
async def read_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a specific role by ID, including its permissions."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}", status_code=204, summary="Delete a role")
async def delete_existing_role(
    role_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Delete a role by ID."""
    success = await delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="ROLE_DELETED",
        resource=f"roles/{role_id}",
        details=f"Role {role_id} deleted.",
        ip_address=request.client.host if request.client else None
    ))
    return None


@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleSchema, summary="Add permission to role")
async def add_permission_to_role(
    role_id: int,
    permission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Assign a permission to a role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    perm = await get_permission(db, permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    if perm in role.permissions:
        raise HTTPException(status_code=400, detail="Permission already assigned to this role")
    
    role.permissions.append(perm)
    await db.commit()
    await db.refresh(role)
    
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="PERMISSION_ADDED_TO_ROLE",
        resource=f"roles/{role_id}",
        details=f"Permission '{perm.name}' added to role '{role.name}'.",
        ip_address=request.client.host if request.client else None
    ))
    return role


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleSchema, summary="Remove permission from role")
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Remove a permission from a role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    perm = await get_permission(db, permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    if perm not in role.permissions:
        raise HTTPException(status_code=400, detail="Permission is not assigned to this role")
    
    role.permissions.remove(perm)
    await db.commit()
    await db.refresh(role)
    
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="PERMISSION_REMOVED_FROM_ROLE",
        resource=f"roles/{role_id}",
        details=f"Permission '{perm.name}' removed from role '{role.name}'.",
        ip_address=request.client.host if request.client else None
    ))
    return role


@router.get("/{role_id}/permissions", response_model=List[PermissionSchema], summary="List permissions for role")
async def list_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """List all permissions assigned to a specific role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role.permissions
