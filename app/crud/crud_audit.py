from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate

async def log_action(db: AsyncSession, audit: AuditLogCreate) -> AuditLog:
    db_audit = AuditLog(
        user_id=audit.user_id,
        action=audit.action,
        resource=audit.resource,
        details=audit.details,
        ip_address=audit.ip_address
    )
    db.add(db_audit)
    await db.commit()
    await db.refresh(db_audit)
    return db_audit

async def get_audit_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AuditLog]:
    result = await db.execute(select(AuditLog).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit))
    return result.scalars().all()

async def get_audit_logs_for_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(desc(AuditLog.timestamp))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_audit_log(db: AsyncSession, log_id: int) -> Optional[AuditLog]:
    result = await db.execute(select(AuditLog).filter(AuditLog.id == log_id))
    return result.scalars().first()
