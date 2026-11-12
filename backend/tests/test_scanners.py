from pathlib import Path

from app.scanners import bandit_scanner, mypy_scanner, ruff_scanner

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_bandit_finds_eval():
    findings = bandit_scanner.scan(SAMPLES)
    assert any(f.rule_id == "B307" and f.file.endswith("utils.py") for f in findings)


def test_ruff_finds_undefined_name():
    findings = ruff_scanner.scan(SAMPLES)
    assert any(f.rule_id == "F821" for f in findings)


def test_mypy_finds_wrong_return_type():
    findings = mypy_scanner.scan(SAMPLES)
    assert any(f.rule_id == "return-value" and f.file.endswith("bugs.py") for f in findings)