import ast
from pathlib import Path


def read_source(root: Path, rel_file: str) -> str | None:
    root = Path(root).resolve()
    path = (root / rel_file).resolve()
    if not path.is_relative_to(root):  # never read outside the project
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def get_code_block(source: str, line: int, radius: int = 12) -> tuple[int, int]:
    """Return (start, end), 1-based and inclusive.

    This is the enclosing function if it is small enough,
    otherwise a window around the flagged line.
    """
    lines = source.splitlines()
    start, end = max(1, line - radius), min(len(lines), line + radius)
    try:
        tree = ast.parse(source)
        best = None
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.lineno <= line <= node.end_lineno
                and (best is None or node.lineno > best.lineno)
            ):
                best = node
        if best and (best.end_lineno - best.lineno) <= 60:
            start, end = best.lineno, best.end_lineno
    except (SyntaxError, ValueError):
        pass
    return start, end


def get_code_context(root: Path, rel_file: str, line: int, radius: int = 12) -> str:
    source = read_source(root, rel_file)
    if source is None:
        return ""
    lines = source.splitlines()
    start, end = get_code_block(source, line, radius)
    return "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))