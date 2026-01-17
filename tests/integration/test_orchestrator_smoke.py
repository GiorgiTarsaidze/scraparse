from pathlib import Path

from scraparse.adapters.llm.base import LLMClient, Message
from scraparse.cli.schema_editor import SchemaEditor
from scraparse.core.limits import Limits
from scraparse.core.models import FetchResult, RunSpec
from scraparse.core.paths import templates_dir
from scraparse.core.workspace import WorkspaceManager
from scraparse.core.limits import LimitTracker
from scraparse.engine.orchestrator import Orchestrator, OrchestratorDeps
from scraparse.plugins.ai.prompt_renderer import PromptPack, PromptRenderer
from scraparse.plugins.ai.schema_generator import SchemaGenerator
from scraparse.plugins.ai.script_generator import ScriptGenerator
from scraparse.plugins.fetchers.base import Fetcher


class FakeLLM(LLMClient):
    def complete(self, messages: list[Message], model: str = "test-model", temperature: float = 0) -> str:
        content = messages[-1].content
        if "FieldSchema JSON" in content:
            return """
import csv
from bs4 import BeautifulSoup
import sys

def main():
    writer = csv.DictWriter(sys.stdout, fieldnames=["product_name"])
    writer.writeheader()
    for path in sys.argv[1:]:
        writer.writerow({"product_name": "Widget"})

if __name__ == "__main__":
    main()
"""
        return '{"fields": [{"name": "product_name", "type": "string", "required": true, "description": "", "example": ""}]}'


class FakeFetcher(Fetcher):
    def fetch(self, url: str, tracker: LimitTracker) -> FetchResult:
        tracker.start_page()
        tracker.add_bytes(10)
        tracker.finish_page()
        return FetchResult(
            url=url,
            content_bytes=b"<html></html>",
            content_text="<html></html>",
            status_code=200,
            content_type="text/html",
        )


class NoopSchemaEditor(SchemaEditor):
    def confirm(self, schema):  # type: ignore[override]
        return schema


def test_orchestrator_smoke(tmp_path: Path) -> None:
    renderer = PromptRenderer(templates_dir(), PromptPack("default"))
    llm = FakeLLM()
    deps = OrchestratorDeps(
        schema_generator=SchemaGenerator(llm, renderer),
        script_generator=ScriptGenerator(llm, renderer),
        fetcher=FakeFetcher(),
        workspace=WorkspaceManager(tmp_path),
        schema_editor=NoopSchemaEditor(),
    )
    orchestrator = Orchestrator(deps)
    spec = RunSpec(
        url="https://example.com",
        discover=False,
        discover_strategy="none",
        prompt="Extract product_name",
        context="",
        promptpack="default",
        save_artifacts=False,
        mode="wizard",
        limits=Limits(),
    )
    outcome = orchestrator.run(spec)
    assert Path(outcome.parser_path).exists()
    assert Path(outcome.report_path).exists()
