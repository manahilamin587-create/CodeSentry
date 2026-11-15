import ast
import hashlib
from pathlib import Path

from app.ai.context import read_source
from app.ai.fixer import Proposal


class ApplyError(Exception):
    pass


def apply_proposal(proposal: Proposal, root: Path) -> str:
    """Write an approved fix to disk. Returns the original file text (for rollback)."""
    root = Path(root).resolve()
    path = (root / proposal.file).resolve()
    if not path.is_relative_to(root):
        raise ApplyError("The file is outside the project.")

    source = read_source(root, proposal.file)
    if source is None:
        raise ApplyError("Could not read the file.")

    # Refuse to apply if the file changed after the fix was proposed
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != proposal.file_sha256:
        raise ApplyError(
            "The file changed after the fix was proposed. Request a new proposal."
        )

    lines = source.splitlines()
    new_lines = (
        lines[: proposal.start_line - 1]
        + proposal.fixed_block.splitlines()
        + lines[proposal.end_line :]
    )
    new_text = "\n".join(new_lines) + ("\n" if source.endswith("\n") else "")

    try:
        ast.parse(new_text)
    except SyntaxError as e:
        raise ApplyError(f"The fix is not valid Python (line {e.lineno}). Nothing was changed.")

    path.write_text(new_text, encoding="utf-8")
    return source