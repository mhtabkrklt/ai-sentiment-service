# Оптимизация инференса
# Логирование
import logging
import time

import numpy as np
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification

from app.config import settings
from app.ml.base import BaseSentimentModel, LABEL_MAP

logger = logging.getLogger(__name__)


class OnnxSentimentModel(BaseSentimentModel):
    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._ready = False

    def load(self) -> None:
        logger.info("Loading ONNX model %s ...", settings.model_name)
        start = time.time()
        self._tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name, cache_dir=settings.model_cache_dir
        )
        self._model = ORTModelForSequenceClassification.from_pretrained(
            settings.model_name,
            export=True,
            cache_dir=settings.model_cache_dir,
        )
        elapsed = (time.time() - start) * 1000
        logger.info("ONNX model loaded in %.0f ms", elapsed)
        self._ready = True

    def predict(self, text: str) -> dict:
        if not self._ready:
            raise RuntimeError("ONNX model is not loaded")
        start = time.time()
        inputs = self._tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            max_length=settings.max_text_length,
        )
        outputs = self._model(**inputs)
        logits = outputs.logits[0]
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()
        all_scores = {
            LABEL_MAP[i]: round(float(probs[i]), 4)
            for i in range(len(probs))
        }
        top_idx = int(np.argmax(probs))
        elapsed_ms = (time.time() - start) * 1000
        logger.info("ONNX inference completed in %.1f ms", elapsed_ms)
        return {
            "label": LABEL_MAP[top_idx],
            "confidence": round(float(probs[top_idx]), 4),
            "all_scores": all_scores,
            "elapsed_ms": round(elapsed_ms, 2),
        }

    def is_ready(self) -> bool:
        return self._ready
