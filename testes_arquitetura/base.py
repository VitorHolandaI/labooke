"""Interface comum para todos os retrievers de teste."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Hit:
    book_id: int
    page_start: int
    snippet: str
    score: float


class Retriever(ABC):
    """Recebe uma query em texto, retorna hits ordenados por relevância."""

    @abstractmethod
    def search(self, query: str, *, k: int = 10) -> list[Hit]: ...

    @property
    def name(self) -> str:
        return type(self).__name__
