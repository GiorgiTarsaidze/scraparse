from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from scraparse.adapters.llm.openai_adapter import OpenAIClient
from scraparse.cli.flags import parse_args
from scraparse.cli.schema_editor import SchemaEditor
from scraparse.cli.wizard import collect_run_spec
from scraparse.core.errors import ConfigError
from scraparse.core.logging import setup_logging
from scraparse.core.limits import Limits
from scraparse.core.paths import templates_dir
from scraparse.core.workspace import WorkspaceManager
from scraparse.engine.orchestrator import Orchestrator, OrchestratorDeps
from scraparse.plugins.ai.prompt_renderer import PromptPack, PromptRenderer
from scraparse.plugins.ai.schema_generator import SchemaGenerator
from scraparse.plugins.ai.script_generator import ScriptGenerator
from scraparse.plugins.fetchers.httpx_fetcher import HttpxFetcher


GENERATED_DIR = Path(".scraparse") / "generated"


def main() -> None:
    setup_logging()
    args = parse_args()

    if args.command == "wipe":
        _wipe_generated()
        return

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Please run:")
        print("  export OPENAI_API_KEY=...\n")
        sys.exit(1)

    promptpacks = _available_promptpacks()
    limits = Limits()
    try:
        spec = collect_run_spec(args, limits, promptpacks)
    except ConfigError as exc:
        print(str(exc))
        sys.exit(1)

    renderer = PromptRenderer(templates_dir(), PromptPack(spec.promptpack))
    llm = OpenAIClient()
    schema_generator = SchemaGenerator(llm, renderer) # ai to understand and generate the schema
    script_generator = ScriptGenerator(llm, renderer) # ai to generate the parsing script

    with HttpxFetcher(spec.limits) as fetcher:
        orchestrator = Orchestrator(
            OrchestratorDeps(
                schema_generator=schema_generator,
                script_generator=script_generator,
                fetcher=fetcher,
                workspace=WorkspaceManager(GENERATED_DIR),
                schema_editor=SchemaEditor(),
            )
        )
        outcome = orchestrator.run(spec)

    if outcome.errors:
        for error in outcome.errors:
            print(f"Error: {error}")
        sys.exit(1)

    print(f"Parser script saved to: {outcome.parser_path}")
    print(f"Run report saved to: {outcome.report_path}")


def _available_promptpacks() -> list[str]:
    pack_root = templates_dir() / "promptpacks"
    if not pack_root.exists():
        return ["default"]
    return [path.name for path in pack_root.iterdir() if path.is_dir()]


def _wipe_generated() -> None:
    if GENERATED_DIR.exists():
        confirmation = input(
            f"Delete all generated runs in {GENERATED_DIR}? Type 'wipe' to confirm: "
        ).strip()
        if confirmation != "wipe":
            print("Wipe cancelled")
            return
        shutil.rmtree(GENERATED_DIR)
        print(f"Deleted {GENERATED_DIR}")
    else:
        print("No generated runs found")


if __name__ == "__main__":
    main()
