from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import verify_password, create_access_token
from app.db.database import get_db
from app.crud.crud_user import get_user_by_email, create_user
from app.crud.crud_audit import log_action
from app.schemas.token import Token
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.audit import AuditLogCreate
from app.api.deps import get_current_active_user
from app.models.user import User

settings = get_settings()
router = APIRouter()


@router.post("/login", response_model=Token, summary="Login and get access token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user credentials and return a JWT access token."""
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        await log_action(db, AuditLogCreate(
            action="LOGIN_FAILED",
            resource="auth",
            details=f"Failed login attempt for: {form_data.username}",
            ip_address=request.client.host if request.client else None
        ))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    await log_action(db, AuditLogCreate(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        resource="auth",
        details=f"User {user.email} logged in successfully.",
        ip_address=request.client.host if request.client else None
    ))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserSchema, status_code=201, summary="Register a new user")
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account. Email must be unique."""
    existing = await get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    new_user = await create_user(db, user_in)
    await log_action(db, AuditLogCreate(
        user_id=new_user.id,
        action="USER_REGISTERED",
        resource="auth",
        details=f"New user registered: {new_user.email}",
        ip_address=request.client.host if request.client else None
    ))
    return new_user


@router.post("/token/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
):
    """Issue a new JWT access token for an authenticated user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema, summary="Get current authenticated user")
async def read_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.post("/validate-token", summary="Validate an access token")
async def validate_token(
    current_user: User = Depends(get_current_active_user),
):
    """Validate the provided Bearer token and return basic user info."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser
    }


@router.post("/password/change", summary="Change current user's password")
async def change_password(
    current_password: str,
    new_password: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change the password for the authenticated user."""
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    from app.core.security import get_password_hash
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()
    
    await log_action(db, AuditLogCreate(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        resource="auth",
        details="User changed their password.",
        ip_address=request.client.host if request.client else None
    ))
    return {"message": "Password changed successfully"}
