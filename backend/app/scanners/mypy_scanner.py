import json
import sys
from pathlib import Path

from app.models.finding import Category, Finding, Severity
from app.scanners.base import get_line, relative_path, run_tool


def scan(root: Path) -> list[Finding]:
    root = Path(root).resolve()
    out = run_tool([
        sys.executable, "-m", "mypy", str(root),
        "--output", "json", "--ignore-missing-imports",
        "--no-error-summary", "--exclude", "(^|/)venv/",
    ])

    findings = []
    for raw in out.splitlines():
        try:
            r = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if r.get("severity") != "error":
            continue
        rel = relative_path(r["file"], root)
        line = r["line"]
        code = r.get("code") or "mypy"
        message = r["message"]
        if r.get("hint"):
            message += f" ({r['hint']})"
        findings.append(Finding(
            id=f"mypy-{code}-{rel}-{line}",
            tool="mypy",
            category=Category.BUG,
            rule_id=code,
            severity=Severity.MEDIUM,
            file=rel,
            line=line,
            message=message,
            code_snippet=get_line(root, rel, line),
        ))
    return findings