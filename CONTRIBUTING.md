# Contributing

## Basics

- Use Python 3.12.3.
- Run tests with `pytest`.
- Keep changes small and readable.

## Project architecture

scraparse is a modular monolith with small, explicit plugin interfaces.

- CLI layer (`src/scraparse/cli/`)
  - `main.py` wires dependencies and enforces env checks.
  - `flags.py` defines minimal CLI flags.
  - `wizard.py` handles interactive prompting and run confirmation.
  - `schema_editor.py` provides interactive schema edits.
- Orchestration (`src/scraparse/engine/`)
  - `orchestrator.py` drives the run: schema generation → fetch/discover → script generation → validation → reporting.
- Core domain (`src/scraparse/core/`)
  - `models.py` defines RunSpec, FieldSchema, FetchResult, etc.
  - `limits.py` enforces safety limits and fail-fast behavior.
  - `workspace.py` owns run folder creation and report/artifact writes.
  - `script_validation.py` validates generated parser code via AST allowlist.
- Plugins (`src/scraparse/plugins/`)
  - `ai/` contains schema + script generators (prompted via Jinja templates).
  - `fetchers/` contains HTTP fetchers (httpx only for now).
  - `discovery/` contains strategies: crawl, pagination, listing.
- Adapters (`src/scraparse/adapters/`)
  - `llm/` provides the OpenAI adapter behind a small interface so other providers can be added later.
- Templates (`src/scraparse/templates/`)
  - Jinja promptpacks for schema and script generation.

Key flow:
1) CLI collects RunSpec.
2) Orchestrator generates schema, prompts user to confirm/edit.
3) Fetcher + discovery plugins collect HTML safely with limits enforced.
4) Script generator produces a parser script
5) Workspace manager writes `parser.py` and `run_report.json`.

## For future

- Stabilize discovery strategies and selectors.
- Improve prompts, add better promptpacks.
- Explore new discovery strategies.
- Expand tests, fixtures, and edge-case coverage.
- Add support for other LLMs
