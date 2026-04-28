import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis
from app.db.session import get_db
from app.exceptions import ModelNotReadyException
from app.schemas import AnalyzeRequest, AnalyzeResponse, TaskCreatedResponse
from app.tasks import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sync(request: Request, body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    model = getattr(request.app.state, "model", None)
    if not model or not model.is_ready():
        raise ModelNotReadyException()
    result = model.predict(body.text)
    try:
        db.add(Analysis(text=body.text, **result))
        await db.commit()
    except Exception:
        logger.exception("Failed to save analysis to DB")
        await db.rollback()
    return AnalyzeResponse(**result)


@router.post(
    "/analyze/async",
    response_model=TaskCreatedResponse,
    status_code=202,
)
async def analyze_async(body: AnalyzeRequest):
    task = analyze_sentiment.delay(body.text)
    return JSONResponse(
        status_code=202,
        content={"task_id": task.id, "status": "PENDING"},
    )
