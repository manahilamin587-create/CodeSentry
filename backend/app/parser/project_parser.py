import ast
import re
from pathlib import Path

from pydantic import BaseModel

IGNORED_DIRS = {
    ".venv", "venv", ".git", "__pycache__", "node_modules",
    ".mypy_cache", ".ruff_cache", ".pytest_cache",
}


class FileInfo(BaseModel):
    path: str
    lines: int = 0
    imports: list[str] = []
    functions: list[str] = []
    classes: list[str] = []
    parse_error: str | None = None


class ProjectInfo(BaseModel):
    root: str
    files: list[FileInfo]
    dependencies: list[str]
    local_dependency_map: dict[str, list[str]]


def find_python_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.py")
        if not any(part in IGNORED_DIRS for part in p.relative_to(root).parts)
    )


def analyze_file(path: Path, root: Path) -> FileInfo:
    rel = str(path.relative_to(root)).replace("\\", "/")
    source = path.read_text(encoding="utf-8", errors="replace")
    info = FileInfo(path=rel, lines=len(source.splitlines()))
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        info.parse_error = f"line {e.lineno}: {e.msg}"
        return info

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            info.imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            info.imports.append(node.module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info.functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            info.classes.append(node.name)
    return info


def read_requirements(root: Path) -> list[str]:
    names: set[str] = set()
    for req in root.rglob("requirements*.txt"):
        if any(part in IGNORED_DIRS for part in req.relative_to(root).parts):
            continue
        for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-"):
                names.add(re.split(r"[=<>!~\[;\s]", line)[0].lower())
    return sorted(names)


def build_local_map(files: list[FileInfo]) -> dict[str, list[str]]:
    stems = {Path(f.path).stem: f.path for f in files}
    result: dict[str, list[str]] = {}
    for f in files:
        deps = set()
        for imp in f.imports:
            top = imp.split(".")[0]
            if top in stems and stems[top] != f.path:
                deps.add(stems[top])
        result[f.path] = sorted(deps)
    return result


def parse_project(root_path: str | Path) -> ProjectInfo:
    root = Path(root_path).resolve()
    files = [analyze_file(p, root) for p in find_python_files(root)]
    return ProjectInfo(
        root=str(root),
        files=files,
        dependencies=read_requirements(root),
        local_dependency_map=build_local_map(files),
    )