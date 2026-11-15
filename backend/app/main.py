from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.ai.applier import ApplyError, apply_proposal
from app.ai.explainer import Explanation, explain_finding
from app.ai.fixer import FixError, Proposal, propose_fix
from app.db import get_proposal, init_db, save_proposal, set_status
from app.models.finding import Finding
from fastapi.middleware.cors import CORSMiddleware
from app.parser.project_parser import ProjectInfo, parse_project
from app.scanners import (
    bandit_scanner,
    mypy_scanner,
    pip_audit_scanner,
    ruff_scanner,
)

app = FastAPI(title="CodeSentry", version="0.1.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class ExplainRequest(BaseModel):
    project_path: str
    finding: Finding


class ProposalRecord(BaseModel):
    id: int
    status: str
    proposal: Proposal


class DecisionResponse(BaseModel):
    id: int
    status: str
    message: str


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


@app.post("/explain", response_model=Explanation)
def explain(req: ExplainRequest):
    root = Path(req.project_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a folder: {req.project_path}")
    try:
        return explain_finding(req.finding, root)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI request failed: {e}")


def _load(proposal_id: int):
    row = get_proposal(proposal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return row, Proposal.model_validate_json(row["proposal_json"])


@app.post("/propose-fix", response_model=ProposalRecord)
def propose(req: ExplainRequest):
    root = Path(req.project_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a folder: {req.project_path}")
    try:
        proposal = propose_fix(req.finding, root)
    except FixError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI request failed: {e}")

    proposal_id = save_proposal(
        req.project_path, req.finding.model_dump_json(), proposal.model_dump_json()
    )
    return ProposalRecord(id=proposal_id, status="pending", proposal=proposal)


@app.get("/proposals/{proposal_id}", response_model=ProposalRecord)
def read_proposal(proposal_id: int):
    row, proposal = _load(proposal_id)
    return ProposalRecord(id=row["id"], status=row["status"], proposal=proposal)


@app.post("/proposals/{proposal_id}/reject", response_model=DecisionResponse)
def reject(proposal_id: int):
    row, _ = _load(proposal_id)
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Proposal is already {row['status']}.")
    set_status(proposal_id, "rejected")
    return DecisionResponse(
        id=proposal_id, status="rejected", message="Fix rejected. No files were changed."
    )


@app.post("/proposals/{proposal_id}/approve", response_model=DecisionResponse)
def approve(proposal_id: int):
    row, proposal = _load(proposal_id)
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Proposal is already {row['status']}.")
    try:
        original = apply_proposal(proposal, Path(row["project_path"]))
    except ApplyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    set_status(proposal_id, "applied", original_source=original)
    return DecisionResponse(
        id=proposal_id,
        status="applied",
        message="Fix approved and applied. Tests have not been run yet.",
    )