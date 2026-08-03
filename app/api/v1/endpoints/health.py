from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """Basic health check endpoint for monitoring and load balancers."""
    return {"status": "healthy", "service": "AuthVault"}


@router.get("/metrics", summary="Service metrics")
async def metrics():
    """Return basic service metrics for monitoring dashboards."""
    import time
    return {
        "service": "AuthVault",
        "uptime_check": True,
        "timestamp": time.time(),
        "version": "1.0.0"
    }
