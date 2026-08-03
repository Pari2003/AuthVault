from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.crud.crud_user import get_user, get_users, create_user, update_user, delete_user, get_user_by_email
from app.crud.crud_audit import log_action
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.schemas.audit import AuditLogCreate
from app.api.deps import get_current_active_user, get_current_superuser, require_permission
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[UserSchema], summary="List all users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_permission("users:read")),
):
    """Retrieve a paginated list of all users. Requires 'users:read' permission."""
    users = await get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserSchema, status_code=201, summary="Create a new user")
async def create_new_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:create")),
):
    """Create a new user. Requires 'users:create' permission."""
    existing = await get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await create_user(db, user_in)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_CREATED",
        resource=f"users/{new_user.id}",
        details=f"Admin created user: {new_user.email}",
        ip_address=request.client.host if request.client else None
    ))
    return new_user


@router.get("/me", response_model=UserSchema, summary="Get my profile")
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserSchema, summary="Update my profile")
async def update_user_me(
    user_in: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the profile of the currently authenticated user."""
    # Prevent self-escalation
    user_in.is_superuser = None
    user_in.role_id = None
    updated = await update_user(db, current_user.id, user_in)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_SELF_UPDATED",
        resource=f"users/{current_user.id}",
        details="User updated their own profile.",
        ip_address=request.client.host if request.client else None
    ))
    return updated


@router.get("/{user_id}", response_model=UserSchema, summary="Get user by ID")
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_permission("users:read")),
):
    """Retrieve a specific user by ID. Requires 'users:read' permission."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserSchema, summary="Update user by ID")
async def update_existing_user(
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:update")),
):
    """Update a specific user. Requires 'users:update' permission."""
    updated = await update_user(db, user_id, user_in)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_UPDATED",
        resource=f"users/{user_id}",
        details=f"Admin updated user {user_id}.",
        ip_address=request.client.host if request.client else None
    ))
    return updated


@router.delete("/{user_id}", status_code=204, summary="Delete user by ID")
async def delete_existing_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:delete")),
):
    """Delete a user by ID. Requires 'users:delete' permission."""
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_DELETED",
        resource=f"users/{user_id}",
        details=f"Admin deleted user {user_id}.",
        ip_address=request.client.host if request.client else None
    ))
    return None


@router.post("/{user_id}/role/{role_id}", response_model=UserSchema, summary="Assign role to user")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Assign a role to a user. Requires superuser privileges."""
    from app.crud.crud_role import get_role
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role_id = role_id
    await db.commit()
    await db.refresh(user)
    
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="ROLE_ASSIGNED",
        resource=f"users/{user_id}",
        details=f"Assigned role '{role.name}' to user {user_id}.",
        ip_address=request.client.host if request.client else None
    ))
    return user


@router.delete("/{user_id}/role", response_model=UserSchema, summary="Remove role from user")
async def remove_role_from_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Remove the assigned role from a user. Requires superuser privileges."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role_id = None
    await db.commit()
    await db.refresh(user)
    
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="ROLE_REMOVED",
        resource=f"users/{user_id}",
        details=f"Removed role from user {user_id}.",
        ip_address=request.client.host if request.client else None
    ))
    return user


@router.post("/{user_id}/activate", response_model=UserSchema, summary="Activate user")
async def activate_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Activate a deactivated user account. Requires superuser privileges."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_ACTIVATED",
        resource=f"users/{user_id}",
        details=f"User {user_id} activated.",
        ip_address=request.client.host if request.client else None
    ))
    return user


@router.post("/{user_id}/deactivate", response_model=UserSchema, summary="Deactivate user")
async def deactivate_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Deactivate a user account. Requires superuser privileges."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="USER_DEACTIVATED",
        resource=f"users/{user_id}",
        details=f"User {user_id} deactivated.",
        ip_address=request.client.host if request.client else None
    ))
    return user
