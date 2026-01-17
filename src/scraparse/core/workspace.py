from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from scraparse.core.util import slugify_domain


@dataclass
class WorkspacePaths:
    run_dir: Path
    artifacts_dir: Path
    html_dir: Path
    parser_path: Path
    report_path: Path
    schema_path: Path


class WorkspaceManager:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def make_run_id(self, url: str, timestamp: str) -> str:
        safe_domain = slugify_domain(url)
        return f"{timestamp}_{safe_domain}"

    def create(self, run_id: str, save_artifacts: bool) -> WorkspacePaths:
        run_dir = self.base_dir / run_id
        artifacts_dir = run_dir / "artifacts"
        html_dir = artifacts_dir / "html"
        run_dir.mkdir(parents=True, exist_ok=True)
        if save_artifacts:
            html_dir.mkdir(parents=True, exist_ok=True)
        parser_path = run_dir / "parser.py"
        report_path = run_dir / "run_report.json"
        schema_path = artifacts_dir / "schema.json"
        return WorkspacePaths(
            run_dir=run_dir,
            artifacts_dir=artifacts_dir,
            html_dir=html_dir,
            parser_path=parser_path,
            report_path=report_path,
            schema_path=schema_path,
        )

    def write_parser(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def write_report(self, path: Path, report: dict[str, object]) -> None:
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def write_schema(self, path: Path, schema: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

    def write_html(self, path: Path, content: bytes) -> None:
        path.write_bytes(content)
