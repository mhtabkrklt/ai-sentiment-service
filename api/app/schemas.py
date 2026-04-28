# Валидация данных
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class AnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Текст для анализа тональности",
        examples=["Отличный фильм!"],
    )


class AnalyzeResponse(BaseModel):
    label: SentimentLabel = Field(description="Метка тональности")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Уверенность модели"
    )
    all_scores: dict[str, float] = Field(
        description="Вероятности всех классов"
    )
    elapsed_ms: float = Field(description="Время инференса в миллисекундах")


class TaskCreatedResponse(BaseModel):
    task_id: str = Field(description="ID созданной задачи")
    status: Literal["PENDING"] = "PENDING"


class TaskStatusResponse(BaseModel):
    task_id: str = Field(description="ID задачи")
    status: Literal["PENDING", "STARTED", "SUCCESS", "FAILURE"] = Field(
        description="Статус задачи"
    )
    result: AnalyzeResponse | None = None
    error: str | None = None
