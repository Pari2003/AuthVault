from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.crud.crud_audit import get_audit_logs, get_audit_logs_for_user, get_audit_log
from app.schemas.audit import AuditLog as AuditLogSchema
from app.api.deps import get_current_superuser, get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[AuditLogSchema], summary="List all audit logs")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a paginated, reverse-chronological list of all audit logs.
    Requires superuser privileges."""
    logs = await get_audit_logs(db, skip=skip, limit=limit)
    return logs


@router.get("/me", response_model=List[AuditLogSchema], summary="List my audit logs")
async def list_my_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve audit logs for the currently authenticated user."""
    logs = await get_audit_logs_for_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return logs


@router.get("/{log_id}", response_model=AuditLogSchema, summary="Get audit log entry by ID")
async def read_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_superuser),
):
    """Retrieve a specific audit log entry by its ID. Requires superuser privileges."""
    log = await get_audit_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return log
