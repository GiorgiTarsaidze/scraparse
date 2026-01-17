from scraparse.core.script_validation import validate_script


def test_valid_script_passes() -> None:
    script = """
import csv
from bs4 import BeautifulSoup

def main():
    pass

if __name__ == "__main__":
    main()
"""
    errors = validate_script(script)
    assert errors == []


def test_forbidden_import_fails() -> None:
    script = """
import os
"""
    errors = validate_script(script)
    assert any("Forbidden import" in err for err in errors)


def test_forbidden_call_fails() -> None:
    script = """

def main():
    eval("1+1")
"""
    errors = validate_script(script)
    assert any("Forbidden call" in err for err in errors)
