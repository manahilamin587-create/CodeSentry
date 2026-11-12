from pathlib import Path

from app.parser.project_parser import parse_project

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_finds_python_files():
    info = parse_project(SAMPLES / "sample_app1")
    names = {f.path for f in info.files}
    assert {"db.py", "config.py", "utils.py", "bugs.py"} <= names


def test_extracts_functions():
    info = parse_project(SAMPLES / "sample_app1")
    utils = next(f for f in info.files if f.path == "utils.py")
    assert "ping_host" in utils.functions


def test_reads_requirements():
    info = parse_project(SAMPLES / "sample_app2")
    assert "requests" in info.dependencies