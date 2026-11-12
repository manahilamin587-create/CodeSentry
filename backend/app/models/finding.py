from enum import Enum
from pydantic import BaseModel, Field


class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Finding(BaseModel):
    id: str = Field(description="Unique id, e.g. bandit-B608-db.py-3")
    tool: str = Field(description="bandit, ruff, mypy, pip-audit, semgrep")
    category: Category
    rule_id: str
    severity: Severity
    file: str
    line: int
    message: str
    code_snippet: str = ""