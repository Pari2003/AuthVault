from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.models.role import Role

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Eagerly load the role (and its permissions via selectin on Role model)
    result = await db.execute(
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .filter(User.id == int(user_id))
    )
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def require_permission(permission_name: str):
    """Dependency factory that checks if the current user's role has a specific permission."""
    async def _check_permission(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        if current_user.role is None:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: '{permission_name}' required."
            )
        
        # role.permissions is eager-loaded via selectin
        user_permissions = {p.name for p in current_user.role.permissions}
        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: '{permission_name}' required."
            )
        return current_user
    return _check_permission
