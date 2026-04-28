# Изоляция ML-логики
from abc import ABC, abstractmethod

LABEL_MAP = {0: "NEUTRAL", 1: "POSITIVE", 2: "NEGATIVE"}


class BaseSentimentModel(ABC):
    @abstractmethod
    def load(self) -> None:
        ...

    @abstractmethod
    def predict(self, text: str) -> dict:
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        ...
