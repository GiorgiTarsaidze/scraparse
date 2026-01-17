from __future__ import annotations

from dataclasses import dataclass

from scraparse.cli.flags import CliArgs
from scraparse.core.errors import ConfigError
from scraparse.core.limits import Limits
from scraparse.core.models import RunSpec
from scraparse.core.util import parse_bool


@dataclass
class WizardInputs:
    url: str
    discover: bool
    prompt: str
    context: str
    promptpack: str
    save_artifacts: bool
    next_selector: str | None
    limits: Limits


def _prompt_text(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def _prompt_bool(label: str, default: bool) -> bool:
    default_text = "y" if default else "n"
    while True:
        value = input(f"{label} [y/n] (default {default_text}): ").strip()
        if not value:
            return default
        try:
            return parse_bool(value)
        except ValueError:
            print("Please enter y or n.")


def _prompt_int(label: str, default: int) -> int:
    while True:
        value = input(f"{label} [default {default}]: ").strip()
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a number.")


def collect_run_spec(args: CliArgs, limits: Limits, promptpacks: list[str]) -> RunSpec:
    mode = _detect_mode(args)
    url = args.url or _prompt_text("Target URL")
    if args.discover_mode:
        discover = True
    elif args.discover:
        discover = True
    else:
        discover = _prompt_bool("Enable discovery", False)
    if discover:
        discover_strategy = args.discover_mode or _prompt_choice(
            "Discovery strategy",
            ["crawl", "pagination", "listing"],
            "crawl",
        )
    else:
        discover_strategy = "none"
    prompt = args.prompt or _prompt_text("Extraction prompt")
    context = args.context or _prompt_text("Context notes (optional)", "")
    promptpack_default = args.promptpack or (promptpacks[0] if promptpacks else "default")
    promptpack = _prompt_text("Prompt pack", promptpack_default)
    if promptpack not in promptpacks:
        promptpack = promptpack_default
    next_selector = args.next_selector
    if discover_strategy == "pagination" and not next_selector:
        next_selector = _prompt_text("Next-page CSS selector (optional)", "") or None
    detail_selector = args.detail_selector
    if discover_strategy == "listing" and not detail_selector:
        detail_selector = _prompt_text("Detail link CSS selector (optional)", "") or None
    save_artifacts = (
        args.save_artifacts
        if args.save_artifacts is not None
        else _prompt_bool("Save artifacts", False)
    )

    if mode == "wizard":
        limits = _prompt_limits(args, limits)
    else:
        limits = limits.with_overrides(args.limits_overrides)

    spec = RunSpec(
        url=url,
        discover=discover,
        discover_strategy=discover_strategy,
        prompt=prompt,
        context=context,
        promptpack=promptpack,
        save_artifacts=save_artifacts,
        mode=mode,
        limits=limits,
        next_selector=next_selector,
        detail_selector=detail_selector,
    )
    _confirm_run_spec(spec)
    return spec


def _prompt_limits(args: CliArgs, limits: Limits) -> Limits:
    if args.limits_overrides:
        limits = limits.with_overrides(args.limits_overrides)
    print("\nSafety limits (press Enter to keep default)")
    max_pages = _prompt_int("Max pages", limits.max_pages)
    max_depth = _prompt_int("Max depth", limits.max_depth)
    max_response_bytes = _prompt_int("Max response bytes", limits.max_response_bytes)
    max_total_bytes = _prompt_int("Max total bytes", limits.max_total_bytes)
    return limits.with_overrides(
        {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "max_response_bytes": max_response_bytes,
            "max_total_bytes": max_total_bytes,
        }
    )


def _detect_mode(args: CliArgs) -> str:
    any_flags = any(
        [
            args.url,
            args.prompt,
            args.context,
            args.promptpack,
            args.discover,
            args.discover_mode,
            args.next_selector,
            args.detail_selector,
            args.save_artifacts is not None,
            any(value is not None for value in args.limits_overrides.values()),
        ]
    )
    return "hybrid" if any_flags else "wizard"


def _confirm_run_spec(spec: RunSpec) -> None:
    print("\nRun configuration:")
    print(f"- URL: {spec.url}")
    print(f"- Mode: {spec.mode}")
    print(f"- Discovery: {spec.discover}")
    print(f"- Discovery strategy: {spec.discover_strategy}")
    print(f"- Prompt pack: {spec.promptpack}")
    print(f"- Save artifacts: {spec.save_artifacts}")
    print(f"- Max pages: {spec.limits.max_pages}")
    print(f"- Max depth: {spec.limits.max_depth}")
    print(f"- Max response bytes: {spec.limits.max_response_bytes}")
    print(f"- Max total bytes: {spec.limits.max_total_bytes}")
    if spec.next_selector:
        print(f"- Next selector: {spec.next_selector}")
    if spec.detail_selector:
        print(f"- Detail selector: {spec.detail_selector}")
    if not _prompt_bool("Proceed", True):
        raise ConfigError("Run cancelled by user")


def _prompt_choice(label: str, options: list[str], default: str) -> str:
    options_text = "/".join(options)
    while True:
        value = input(f"{label} ({options_text}) [default {default}]: ").strip().lower()
        if not value:
            return default
        if value in options:
            return value
        print(f"Please choose one of: {options_text}")
