from __future__ import annotations

from scraparse.adapters.llm.base import LLMClient, Message
from scraparse.plugins.ai.prompt_renderer import PromptRenderer


class ScriptGenerator:
    def __init__(self, llm: LLMClient, renderer: PromptRenderer) -> None:
        self.llm = llm
        self.renderer = renderer

    def generate(
        self,
        schema_json: str,
        html_samples: list[str],
        validation_errors: list[str] | None = None,
    ) -> str:
        system_prompt = self.renderer.render(
            "script_generator_system_prompt.jinja",
            {},
        )
        user_prompt = self.renderer.render(
            "script_generator_user_prompt.jinja",
            {
                "schema_json": schema_json,
                "html_samples": html_samples,
                "validation_errors": validation_errors or [],
            },
        )
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]
        return self.llm.complete(messages, temperature=0)
