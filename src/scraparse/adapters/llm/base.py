from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    role: str
    content: str


class LLMClient(Protocol):
    def complete(self, messages: list[Message], model: str, temperature: float) -> str:
        ...
