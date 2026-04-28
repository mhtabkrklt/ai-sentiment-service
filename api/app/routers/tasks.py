# Асинхронная очередь задач
import asyncio
import json

from celery.result import AsyncResult
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.celery_app import celery
from app.schemas import TaskStatusResponse

router = APIRouter()


def _build_task_response(task_id: str) -> dict:
    result = AsyncResult(task_id, app=celery)
    state = result.state
    response = {"task_id": task_id, "status": state, "result": None, "error": None}
    if state == "SUCCESS":
        response["result"] = result.result
    elif state == "FAILURE":
        response["error"] = str(result.result)
    return response


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    return _build_task_response(task_id)


_WS_MAX_POLLS = 240  # 240 × 0.5s = 120 seconds max


@router.websocket("/ws/tasks/{task_id}")
async def ws_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        for _ in range(_WS_MAX_POLLS):
            data = _build_task_response(task_id)
            await websocket.send_text(json.dumps(data))
            if data["status"] in ("SUCCESS", "FAILURE"):
                await websocket.close()
                return
            await asyncio.sleep(0.5)
        await websocket.close(code=1001)
    except WebSocketDisconnect:
        pass
