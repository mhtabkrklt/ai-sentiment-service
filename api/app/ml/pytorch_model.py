# Изоляция ML-логики
# Управление ресурсами
# Логирование
import logging
import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings
from app.ml.base import BaseSentimentModel, LABEL_MAP

logger = logging.getLogger(__name__)


class SentimentModel(BaseSentimentModel):
    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._ready = False

    def load(self) -> None:
        logger.info("Loading PyTorch model %s ...", settings.model_name)
        start = time.time()
        self._tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name, cache_dir=settings.model_cache_dir
        )
        self._model = AutoModelForSequenceClassification.from_pretrained(
            settings.model_name, cache_dir=settings.model_cache_dir
        )
        self._model.eval()
        elapsed = (time.time() - start) * 1000
        logger.info("Model loaded in %.0f ms", elapsed)
        self._ready = True

    def predict(self, text: str) -> dict:
        start = time.time()
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=settings.max_text_length,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]
        all_scores = {
            LABEL_MAP[i]: round(probs[i].item(), 4) for i in range(len(probs))
        }
        top_idx = probs.argmax().item()
        elapsed_ms = (time.time() - start) * 1000
        logger.info("Inference completed in %.1f ms", elapsed_ms)
        return {
            "label": LABEL_MAP[top_idx],
            "confidence": round(probs[top_idx].item(), 4),
            "all_scores": all_scores,
            "elapsed_ms": round(elapsed_ms, 2),
        }

    def is_ready(self) -> bool:
        return self._ready
