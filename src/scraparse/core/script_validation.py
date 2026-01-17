from __future__ import annotations

import ast

ALLOWED_IMPORTS = {
    "bs4",
    "re",
    "json",
    "typing",
    "dataclasses",
    "html",
    "urllib.parse",
    "sys",
    "csv",
    "pathlib",
}

FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}


def validate_script(script: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(script)
    except SyntaxError as exc:
        return [f"Syntax error: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORTS:
                    errors.append(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module not in ALLOWED_IMPORTS:
                errors.append(f"Forbidden import: {module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                errors.append(f"Forbidden call: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_CALLS:
                errors.append(f"Forbidden call: {node.func.attr}")
    return errors
