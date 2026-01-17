from __future__ import annotations

import json

from scraparse.adapters.llm.base import LLMClient, Message
from scraparse.core.errors import AIError
from scraparse.core.models import FieldSchema
from scraparse.plugins.ai.prompt_renderer import PromptRenderer


class SchemaGenerator:
    def __init__(self, llm: LLMClient, renderer: PromptRenderer) -> None:
        self.llm = llm
        self.renderer = renderer

    def generate(self, user_prompt: str, context: str) -> FieldSchema:
        system_prompt = self.renderer.render(
            "schema_generator_system_prompt.jinja",
            {},
        )
        base_user_prompt = self.renderer.render(
            "schema_generator_user_prompt.jinja",
            {"user_prompt": user_prompt, "context": context},
        )
        messages = [Message(role="system", content=system_prompt)]
        last_error: Exception | None = None
        for attempt in range(3):
            user_prompt_text = base_user_prompt
            if attempt > 0:
                user_prompt_text += (
                    "\n\nThe previous response was invalid JSON or invalid schema. "
                    "Return only valid JSON matching the required schema."
                )
            messages_with_user = messages + [Message(role="user", content=user_prompt_text)]
            raw = self.llm.complete(messages_with_user, temperature=0)
            try:
                data = json.loads(raw)
                return FieldSchema.from_dict(data)
            except Exception as exc:
                last_error = exc
        raise AIError(f"Schema generation failed: {last_error}")
