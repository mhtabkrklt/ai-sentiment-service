# ORM
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis
from app.db.session import get_db

router = APIRouter()


@router.get("/history")
async def get_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "text": r.text[:100] + "..." if len(r.text) > 100 else r.text,
            "label": r.label,
            "confidence": r.confidence,
            "all_scores": r.all_scores,
            "elapsed_ms": r.elapsed_ms,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
