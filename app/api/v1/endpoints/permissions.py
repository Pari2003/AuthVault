from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.crud.crud_role import get_permission, get_permissions, create_permission, delete_permission
from app.crud.crud_audit import log_action
from app.schemas.role import Permission as PermissionSchema, PermissionCreate
from app.schemas.audit import AuditLogCreate
from app.api.deps import get_current_superuser
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[PermissionSchema], summary="List all permissions")
async def list_permissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a paginated list of all permissions."""
    perms = await get_permissions(db, skip=skip, limit=limit)
    return perms


@router.post("/", response_model=PermissionSchema, status_code=201, summary="Create a new permission")
async def create_new_permission(
    perm_in: PermissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Create a new permission. Permission name must be unique."""
    from sqlalchemy.future import select
    from app.models.role import Permission
    result = await db.execute(select(Permission).filter(Permission.name == perm_in.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Permission with this name already exists")
    
    new_perm = await create_permission(db, perm_in)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="PERMISSION_CREATED",
        resource=f"permissions/{new_perm.id}",
        details=f"Permission '{new_perm.name}' created.",
        ip_address=request.client.host if request.client else None
    ))
    return new_perm


@router.get("/{permission_id}", response_model=PermissionSchema, summary="Get permission by ID")
async def read_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a specific permission by ID."""
    perm = await get_permission(db, permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


@router.delete("/{permission_id}", status_code=204, summary="Delete a permission")
async def delete_existing_permission(
    permission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Delete a permission by ID."""
    success = await delete_permission(db, permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="PERMISSION_DELETED",
        resource=f"permissions/{permission_id}",
        details=f"Permission {permission_id} deleted.",
        ip_address=request.client.host if request.client else None
    ))
    return None
