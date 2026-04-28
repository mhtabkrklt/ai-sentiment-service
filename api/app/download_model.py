"""Init-container script: downloads/caches model before api/worker start."""
import logging

logging.basicConfig(level="INFO", format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings

if settings.use_onnx:
    from app.ml.onnx_model import OnnxSentimentModel
    model = OnnxSentimentModel()
else:
    from app.ml.pytorch_model import SentimentModel
    model = SentimentModel()

logger.info("Downloading / verifying model cache for: %s", settings.model_name)
model.load()
logger.info("Model ready — init complete")
