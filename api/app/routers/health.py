# API Health Check
import redis
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    checks = {"api": True, "model": False, "redis": False, "postgres": False}

    model = getattr(request.app.state, "model", None)
    if model and model.is_ready():
        checks["model"] = True

    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, socket_timeout=2)
    try:
        r.ping()
        checks["redis"] = True
    except Exception:
        pass
    finally:
        r.close()

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = True
    except Exception:
        pass

    all_ok = all(checks.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )
