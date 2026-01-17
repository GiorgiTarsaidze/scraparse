from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass(frozen=True)
class PromptPack:
    name: str


class PromptRenderer:
    def __init__(self, templates_dir: Path, promptpack: PromptPack) -> None:
        self.templates_dir = templates_dir
        self.promptpack = promptpack
        pack_dir = templates_dir / "promptpacks" / promptpack.name
        self.env = Environment(
            loader=FileSystemLoader(str(pack_dir)),
            autoescape=select_autoescape(),
        )

    def render(self, template_name: str, context: dict[str, object]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)
