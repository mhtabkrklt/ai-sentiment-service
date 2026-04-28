import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.exceptions import (
    ModelNotReadyException,
    InvalidPromptException,
    generic_exception_handler,
    invalid_prompt_handler,
    model_not_ready_handler,
)
from app.routers import analyze, health, history, tasks

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _load_model(model):
    try:
        model.load()
    except Exception:
        logger.exception("Model loading failed")


# Управление жизненным циклом
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    if settings.use_onnx:
        from app.ml.onnx_model import OnnxSentimentModel
        model = OnnxSentimentModel()
    else:
        from app.ml.pytorch_model import SentimentModel
        model = SentimentModel()

    # Expose model immediately so /health can report is_ready() = False while loading.
    # Load in background thread so API starts and healthcheck can respond right away.
    app.state.model = model
    thread = threading.Thread(target=_load_model, args=(model,), daemon=True, name="model-loader")
    thread.start()
    logger.info("Model loading in background — API accepting requests")
    yield
    logger.info("Application shutting down")
    app.state.model = None
    logger.info("Application stopped")


app = FastAPI(title="Sentiment Analysis API", lifespan=lifespan)

# Метрики
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Обработка ошибок
app.add_exception_handler(ModelNotReadyException, model_not_ready_handler)
app.add_exception_handler(InvalidPromptException, invalid_prompt_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(health.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(history.router, prefix="/api")
