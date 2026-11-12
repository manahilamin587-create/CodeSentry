import json
import sys
from pathlib import Path

from app.models.finding import Category, Finding, Severity
from app.parser.project_parser import IGNORED_DIRS
from app.scanners.base import run_tool


def _line_of(req_file: Path, package: str) -> int:
    for i, text in enumerate(req_file.read_text(errors="replace").splitlines(), 1):
        if text.strip().lower().startswith(package.lower()):
            return i
    return 1


def scan(root: Path) -> list[Finding]:
    """Check pinned dependencies against known vulnerabilities. Needs internet."""
    root = Path(root).resolve()
    findings = []

    for req in root.rglob("requirements*.txt"):
        rel_parts = req.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue

        out = run_tool([
            sys.executable, "-m", "pip_audit", "-r", str(req),
            "--no-deps", "--disable-pip", "-f", "json",
        ])
        if not out.strip():
            continue

        rel = str(req.relative_to(root)).replace("\\", "/")
        for dep in json.loads(out).get("dependencies", []):
            for vuln in dep.get("vulns", []):
                line = _line_of(req, dep["name"])
                fixes = ", ".join(vuln.get("fix_versions", [])) or "none known"
                findings.append(Finding(
                    id=f"pip-audit-{vuln['id']}-{rel}-{line}",
                    tool="pip-audit",
                    category=Category.SECURITY,
                    rule_id=vuln["id"],
                    severity=Severity.MEDIUM,
                    file=rel,
                    line=line,
                    message=(
                        f"{dep['name']} {dep['version']} has a known vulnerability "
                        f"({vuln['id']}). Fixed in: {fixes}"
                    ),
                    code_snippet=f"{dep['name']}=={dep['version']}",
                ))
        # pip-audit can report the same vulnerability more than once
    return list({f.id: f for f in findings}.values())