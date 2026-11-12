import json
import sys
from pathlib import Path

from app.models.finding import Category, Finding, Severity
from app.scanners.base import relative_path, run_tool

EXCLUDES = "*/.venv/*,*/venv/*,*/node_modules/*,*/.git/*"


def scan(root: Path) -> list[Finding]:
    root = Path(root).resolve()
    out = run_tool([
        sys.executable, "-m", "bandit", "-r", str(root),
        "-f", "json", "-q", "-x", EXCLUDES,
    ])
    if not out.strip():
        return []

    findings = []
    for r in json.loads(out).get("results", []):
        rel = relative_path(r["filename"], root)
        try:
            severity = Severity(r["issue_severity"])
        except ValueError:
            severity = Severity.LOW
        findings.append(Finding(
            id=f"bandit-{r['test_id']}-{rel}-{r['line_number']}",
            tool="bandit",
            category=Category.SECURITY,
            rule_id=r["test_id"],
            severity=severity,
            file=rel,
            line=r["line_number"],
            message=r["issue_text"],
            code_snippet=r.get("code", "").strip(),
        ))
    return findings