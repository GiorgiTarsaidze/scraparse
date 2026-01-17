from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from scraparse.cli.schema_editor import SchemaEditor
from scraparse.core.errors import LimitExceededError, ScraparseError, ValidationError
from scraparse.core.limits import LimitTracker
from scraparse.core.models import FetchResult, RunOutcome, RunSpec
from scraparse.core.script_validation import validate_script
from scraparse.core.util import now_utc_iso
from scraparse.core.workspace import WorkspaceManager
from scraparse.plugins.ai.schema_generator import SchemaGenerator
from scraparse.plugins.ai.script_generator import ScriptGenerator
from scraparse.plugins.discovery.crawl import CrawlDiscovery
from scraparse.plugins.discovery.pagination import PaginationDiscovery
from scraparse.plugins.discovery.listing import ListingDiscovery
from scraparse.plugins.fetchers.base import Fetcher


@dataclass
class OrchestratorDeps:
    schema_generator: SchemaGenerator
    script_generator: ScriptGenerator
    fetcher: Fetcher
    workspace: WorkspaceManager
    schema_editor: SchemaEditor


class Orchestrator:
    def __init__(self, deps: OrchestratorDeps) -> None:
        self.deps = deps

    def run(self, spec: RunSpec) -> RunOutcome:
        start_iso = now_utc_iso()
        run_id = self._make_run_id(spec)
        paths = self.deps.workspace.create(run_id, spec.save_artifacts)
        tracker = LimitTracker(spec.limits)
        errors: list[str] = []
        fetched: list[FetchResult] = []
        parser_path = ""
        schema_dict: dict[str, object] | None = None

        try:
            tracker.check_runtime()
            schema = self.deps.schema_generator.generate(spec.prompt, spec.context)
            schema = self.deps.schema_editor.confirm(schema)
            schema_dict = schema.to_dict()
            if spec.save_artifacts:
                self.deps.workspace.write_schema(paths.schema_path, schema.to_dict())

            tracker.check_runtime()
            fetched = self._fetch_pages(spec, tracker)
            if spec.save_artifacts:
                for idx, result in enumerate(fetched, start=1):
                    html_path = paths.html_dir / f"{idx}.html"
                    self.deps.workspace.write_html(html_path, result.content_bytes)

            html_samples = [result.content_text for result in fetched]
            total_chars = sum(len(sample) for sample in html_samples)
            if total_chars > spec.limits.max_html_chars_for_llm:
                raise LimitExceededError(
                    "max_html_chars_for_llm",
                    "Max HTML chars for LLM exceeded",
                    {"html_chars": total_chars},
                    spec.limits.max_html_chars_for_llm,
                )

            schema_json = self._schema_json_for_prompt(schema.to_dict())
            tracker.check_runtime()
            script = self._generate_valid_script(schema_json, html_samples)
            tracker.check_runtime()
            self.deps.workspace.write_parser(paths.parser_path, script)
            parser_path = str(paths.parser_path)
        except ScraparseError as exc:
            errors.append(self._format_error(exc))
        finally:
            report = self._build_report(
                run_id=run_id,
                start_iso=start_iso,
                spec=spec,
                fetched=fetched,
                errors=errors,
                parser_path=parser_path,
                schema_dict=schema_dict,
                schema_path=str(paths.schema_path) if spec.save_artifacts else None,
                total_bytes=tracker.total_bytes,
                end_iso=now_utc_iso(),
            )
            self.deps.workspace.write_report(paths.report_path, report)

        return RunOutcome(
            run_id=run_id,
            parser_path=parser_path,
            report_path=str(paths.report_path),
            fetched_urls=[result.url for result in fetched],
            errors=errors,
        )

    def _fetch_pages(self, spec: RunSpec, tracker: LimitTracker) -> list[FetchResult]:
        if not spec.discover:
            return [self.deps.fetcher.fetch(spec.url, tracker)]
        if spec.discover_strategy == "pagination":
            plugin = PaginationDiscovery()
        elif spec.discover_strategy == "listing":
            plugin = ListingDiscovery()
        elif spec.discover_strategy == "crawl":
            plugin = CrawlDiscovery()
        else:
            raise ValidationError(f"Unknown discovery strategy: {spec.discover_strategy}")
        return plugin.discover(
            start_url=spec.url,
            fetcher=self.deps.fetcher,
            tracker=tracker,
            limits=spec.limits,
            next_selector=spec.next_selector,
            detail_selector=spec.detail_selector,
        )

    def _schema_json_for_prompt(self, schema: dict[str, object]) -> str:
        import json

        return json.dumps(schema, indent=2)

    def _generate_valid_script(self, schema_json: str, html_samples: list[str]) -> str:
        validation_errors: list[str] = []
        for attempt in range(3):
            script = self.deps.script_generator.generate(schema_json, html_samples, validation_errors)
            validation_errors = validate_script(script)
            if not validation_errors:
                return script
        raise ValidationError("Generated script failed validation: " + "; ".join(validation_errors))

    def _make_run_id(self, spec: RunSpec) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self.deps.workspace.make_run_id(spec.url, timestamp)

    def _format_error(self, exc: ScraparseError) -> str:
        if isinstance(exc, LimitExceededError):
            return f"Limit exceeded: {exc.limit_name} (current={exc.current}, limit={exc.limit})"
        return str(exc)

    def _build_report(
        self,
        run_id: str,
        start_iso: str,
        spec: RunSpec,
        fetched: list[FetchResult],
        errors: list[str],
        parser_path: str,
        schema_dict: dict[str, object] | None,
        schema_path: str | None,
        total_bytes: int,
        end_iso: str,
    ) -> dict[str, object]:
        return {
            "run_id": run_id,
            "started_at": start_iso,
            "ended_at": end_iso,
            "inputs": {
                "url": spec.url,
                "mode": spec.mode,
                "discover": spec.discover,
                "discover_strategy": spec.discover_strategy,
                "prompt": spec.prompt,
                "context": spec.context,
                "promptpack": spec.promptpack,
                "save_artifacts": spec.save_artifacts,
                "next_selector": spec.next_selector,
                "detail_selector": spec.detail_selector,
            },
            "schema": schema_dict,
            "schema_path": schema_path,
            "limits": spec.limits.to_dict(),
            "discovered_urls": [result.url for result in fetched],
            "discovered_count": len(fetched),
            "fetched_count": len(fetched),
            "bytes_total": total_bytes,
            "bytes_per_page": {
                result.url: len(result.content_bytes)
                for result in fetched
            },
            "errors": errors,
            "parser_path": parser_path,
        }
