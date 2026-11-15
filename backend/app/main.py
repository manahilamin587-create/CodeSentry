from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.models.finding import Finding
from app.ai.explainer import Explanation, explain_finding
from app.ai.fixer import FixError, Proposal, propose_fix
from app.parser.project_parser import ProjectInfo, parse_project
from app.scanners import (
    bandit_scanner,
    mypy_scanner,
    pip_audit_scanner,
    ruff_scanner,
)

app = FastAPI(title="CodeSentry", version="0.1.0")

SCANNERS = {
    "bandit": bandit_scanner.scan,
    "ruff": ruff_scanner.scan,
    "mypy": mypy_scanner.scan,
    "pip-audit": pip_audit_scanner.scan,
}


class ScanRequest(BaseModel):
    project_path: str


class ScanResponse(BaseModel):
    project: ProjectInfo
    findings: list[Finding]
    tool_errors: dict[str, str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResponse)
def scan_project(req: ScanRequest):
    root = Path(req.project_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a folder: {req.project_path}")

    project = parse_project(root)

    findings: list[Finding] = []
    tool_errors: dict[str, str] = {}
    for name, scan in SCANNERS.items():
        try:
            findings.extend(scan(root))
        except Exception as e:  # one broken tool must not stop the others
            tool_errors[name] = str(e)

    unique = {f.id: f for f in findings}
    ordered = sorted(unique.values(), key=lambda f: (f.file, f.line))
    return ScanResponse(project=project, findings=ordered, tool_errors=tool_errors)

class ExplainRequest(BaseModel):
    project_path: str
    finding: Finding


@app.post("/explain", response_model=Explanation)
def explain(req: ExplainRequest):
    root = Path(req.project_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a folder: {req.project_path}")
    try:
        return explain_finding(req.finding, root)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI request failed: {e}")

@app.post("/propose-fix", response_model=Proposal)
def propose(req: ExplainRequest):
    root = Path(req.project_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a folder: {req.project_path}")
    try:
        return propose_fix(req.finding, root)
    except FixError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI request failed: {e}")