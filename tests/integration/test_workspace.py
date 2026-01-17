from pathlib import Path

from scraparse.core.workspace import WorkspaceManager


def test_workspace_creates_paths(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path)
    paths = manager.create("run-1", save_artifacts=True)
    assert paths.run_dir.exists()
    assert paths.html_dir.exists()
    manager.write_parser(paths.parser_path, "print('ok')")
    manager.write_report(paths.report_path, {"run_id": "run-1"})
    assert paths.parser_path.exists()
    assert paths.report_path.exists()
