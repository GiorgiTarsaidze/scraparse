from __future__ import annotations

import argparse
from dataclasses import dataclass

from scraparse.core.util import parse_bool


@dataclass
class CliArgs:
    command: str | None
    url: str | None
    discover: bool
    discover_mode: str | None
    prompt: str | None
    context: str | None
    promptpack: str | None
    next_selector: str | None
    detail_selector: str | None
    save_artifacts: bool | None
    limits_overrides: dict[str, object]


def _bool_arg(value: str) -> bool:
    return parse_bool(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraparse")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("wipe", help="Delete all generated runs")

    parser.add_argument("--url")
    parser.add_argument("--discover", action="store_true", help="Enable discovery mode")
    parser.add_argument(
        "--discover-mode",
        choices=["crawl", "pagination", "listing"],
        help="Discovery strategy to use",
    )
    parser.add_argument("--prompt", help="Extraction prompt")
    parser.add_argument("--context", help="Extra notes for extraction")
    parser.add_argument("--promptpack", help="Prompt pack name", default=None)
    parser.add_argument("--next-selector", help="CSS selector for next-page link")
    parser.add_argument("--detail-selector", help="CSS selector for detail links")
    parser.add_argument("--save-artifacts", type=_bool_arg, help="true/false")

    # Limits overrides
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--max-depth", type=int)
    parser.add_argument("--max-consecutive-failures", type=int)
    parser.add_argument("--same-domain-only", type=_bool_arg)
    parser.add_argument("--timeout-connect-s", type=float)
    parser.add_argument("--timeout-read-s", type=float)
    parser.add_argument("--timeout-total-s", type=float)
    parser.add_argument("--retries", type=int)
    parser.add_argument("--backoff-base-s", type=float)
    parser.add_argument("--backoff-max-s", type=float)
    parser.add_argument("--jitter-s", type=float)
    parser.add_argument("--rate-limit-rps", type=float)
    parser.add_argument("--max-response-bytes", type=int)
    parser.add_argument("--max-total-bytes", type=int)
    parser.add_argument("--max-runtime-s", type=int)
    parser.add_argument("--max-html-chars-for-llm", type=int)

    return parser


def parse_args(argv: list[str] | None = None) -> CliArgs:
    parser = build_parser()
    args = parser.parse_args(argv)
    overrides = {
        "max_pages": args.max_pages,
        "max_depth": args.max_depth,
        "max_consecutive_failures": args.max_consecutive_failures,
        "same_domain_only": args.same_domain_only,
        "timeout_connect_s": args.timeout_connect_s,
        "timeout_read_s": args.timeout_read_s,
        "timeout_total_s": args.timeout_total_s,
        "retries": args.retries,
        "backoff_base_s": args.backoff_base_s,
        "backoff_max_s": args.backoff_max_s,
        "jitter_s": args.jitter_s,
        "rate_limit_rps": args.rate_limit_rps,
        "max_response_bytes": args.max_response_bytes,
        "max_total_bytes": args.max_total_bytes,
        "max_runtime_s": args.max_runtime_s,
        "max_html_chars_for_llm": args.max_html_chars_for_llm,
    }
    discover = args.discover or args.discover_mode is not None
    return CliArgs(
        command=args.command,
        url=args.url,
        discover=discover,
        discover_mode=args.discover_mode,
        prompt=args.prompt,
        context=args.context,
        promptpack=args.promptpack,
        next_selector=args.next_selector,
        detail_selector=args.detail_selector,
        save_artifacts=args.save_artifacts,
        limits_overrides=overrides,
    )
