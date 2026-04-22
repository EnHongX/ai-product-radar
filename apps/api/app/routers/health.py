from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    services = {"api": "ok", "database": "ok", "redis": "ok"}
    errors: dict[str, str] = {}

    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - health endpoint must report dependency failures.
        services["database"] = "error"
        errors["database"] = str(exc)

    try:
        redis = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        redis.ping()
    except Exception as exc:  # pragma: no cover
        services["redis"] = "error"
        errors["redis"] = str(exc)

    return {
        "status": "ok" if not errors else "degraded",
        "environment": settings.APP_ENV,
        "services": services,
        "errors": errors,
    }
