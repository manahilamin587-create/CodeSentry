import json
import sys
from pathlib import Path

from app.models.finding import Category, Finding, Severity
from app.scanners.base import get_line, relative_path, run_tool


def scan(root: Path) -> list[Finding]:
    root = Path(root).resolve()
    out = run_tool([
        sys.executable, "-m", "ruff", "check", str(root),
        "--select", "F,E9", "--output-format", "json", "--no-cache",
    ])
    if not out.strip():
        return []

    findings = []
    for r in json.loads(out):
        rel = relative_path(r["filename"], root)
        line = r["location"]["row"]
        code = r["code"] or "SYNTAX"
        # Undefined names and syntax errors are more serious than unused imports
        severity = Severity.MEDIUM if code in ("F821", "E902") or code.startswith("E9") else Severity.LOW
        findings.append(Finding(
            id=f"ruff-{code}-{rel}-{line}",
            tool="ruff",
            category=Category.BUG,
            rule_id=code,
            severity=severity,
            file=rel,
            line=line,
            message=r["message"],
            code_snippet=get_line(root, rel, line),
        ))
    return findings