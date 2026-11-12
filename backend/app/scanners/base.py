import subprocess
from pathlib import Path


def run_tool(args: list[str]) -> str:
    """Run a command and return its output.

    Scanners exit with a non-zero code when they find issues,
    so a non-zero exit is not treated as a failure.
    """
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=120
        )
    except FileNotFoundError:
        raise RuntimeError(f"Tool not found: {args[0]}")
    return result.stdout


def relative_path(filename: str, root: Path) -> str:
    try:
        rel = Path(filename).resolve().relative_to(root.resolve())
    except ValueError:
        rel = Path(filename)
    return str(rel).replace("\\", "/")


def get_line(root: Path, rel_file: str, line: int) -> str:
    try:
        lines = (root / rel_file).read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        return lines[line - 1].strip()
    except (OSError, IndexError):
        return ""