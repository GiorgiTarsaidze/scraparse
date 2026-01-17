from __future__ import annotations

import os
import time
from typing import Iterable

from openai import OpenAI
from openai import APIConnectionError, APIError, RateLimitError

from scraparse.adapters.llm.base import LLMClient, Message
from scraparse.core.errors import AIError, ConfigError


DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str | None = None, retries: int = 2) -> None:
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise ConfigError(
                "OPENAI_API_KEY is not set. Set it in your shell, e.g. 'export OPENAI_API_KEY=...'."
            )
        self.client = OpenAI(api_key=resolved_key)
        self.retries = retries

    def complete(self, messages: list[Message], model: str = DEFAULT_MODEL, temperature: float = 0) -> str:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                return content or ""
            except (RateLimitError, APIConnectionError, APIError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (2**attempt))
            except Exception as exc:  # defensive for unexpected SDK errors
                last_error = exc
                break
        raise AIError(f"OpenAI request failed: {last_error}")
