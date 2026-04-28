# Асинхронная очередь задач
import logging
import threading

from celery.signals import worker_ready

from app.celery_app import celery
from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        if settings.use_onnx:
            from app.ml.onnx_model import OnnxSentimentModel
            instance = OnnxSentimentModel()
        else:
            from app.ml.pytorch_model import SentimentModel
            instance = SentimentModel()
        logger.info("Celery worker: loading model...")
        try:
            instance.load()
        except Exception:
            logger.exception("Celery worker: model load failed")
            raise
        logger.info("Celery worker: model loaded")
        _model = instance
    return _model


@worker_ready.connect
def preload_model(**kwargs):
    """Load model at worker startup so first task doesn't hang."""
    _get_model()


@celery.task(name="analyze_sentiment", bind=True)
def analyze_sentiment(self, text: str):
    logger.info("Task %s started", self.request.id)
    model = _get_model()
    result = model.predict(text)
    logger.info("Task %s finished", self.request.id)
    return result
