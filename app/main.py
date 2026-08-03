import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("authvault")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager – creates tables on startup."""
    from app.db.database import engine, Base
    # Import all models so Base.metadata knows about them
    from app.models.user import User  # noqa: F401
    from app.models.role import Role, Permission  # noqa: F401
    from app.models.audit import AuditLog  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("AuthVault started – database tables ensured.")
    yield
    await engine.dispose()
    logger.info("AuthVault shutdown – database connections closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AuthVault is a secure Identity & Access Management (IAM) service "
        "providing JWT-based authentication, role-based access control (RBAC), "
        "OAuth2 login flows, and structured audit logging."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
