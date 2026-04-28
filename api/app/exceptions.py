# Обработка ошибок
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ModelNotReadyException(Exception):
    pass


class InvalidPromptException(Exception):
    def __init__(self, message: str = "Invalid prompt"):
        self.message = message


async def model_not_ready_handler(
    request: Request, exc: ModelNotReadyException
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "ServiceUnavailable",
            "message": "ML model is not loaded yet. Please try again later.",
        },
    )


async def invalid_prompt_handler(
    request: Request, exc: InvalidPromptException
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": "BadRequest", "message": exc.message},
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception for %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred.",
        },
    )
