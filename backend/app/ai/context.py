import ast
from pathlib import Path


def get_code_context(root: Path, rel_file: str, line: int, radius: int = 12) -> str:
    root = Path(root).resolve()
    path = (root / rel_file).resolve()
    if not path.is_relative_to(root):  # never read outside the project
        return ""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

    lines = source.splitlines()
    start, end = max(1, line - radius), min(len(lines), line + radius)

    # If the line is inside a function, send that whole function instead
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

    return "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))