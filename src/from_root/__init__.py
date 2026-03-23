from __future__ import annotations

from pathlib import Path
import inspect
from typing import Iterable, Optional, Union


_MARKERS = (
    ".project-root",   # your explicit marker
    ".git",            # git repo root
    "pyproject.toml",  # common Python project root markers
    "setup.cfg",
    "setup.py",
    "requirements.txt",
)


def _caller_start_dir() -> Path:
    """
    Pick a stable start directory based on the first caller outside this module.
    This avoids Windows/traceback oddities and works when imported from anywhere.
    """
    for frame_info in inspect.stack()[2:]:
        filename = frame_info.filename
        if filename and "from_root.py" not in filename.replace("\\", "/"):
            return Path(filename).resolve().parent
    return Path.cwd().resolve()


def _find_root(start: Path, markers: Iterable[str]) -> Path:
    """
    Walk upwards from `start` until a marker is found.
    """
    start = start.resolve()
    candidates = [start, *start.parents]
    for parent in candidates:
        for m in markers:
            if (parent / m).exists():
                return parent
    # If nothing is found, fall back to cwd (better than Home for most dev setups)
    return Path.cwd().resolve()


def from_root(
    *paths: Union[str, Path],
    start: Optional[Union[str, Path]] = None,
    markers: Iterable[str] = _MARKERS,
    mkdirs: bool = False,
) -> Path:
    """
    Return the detected project root, optionally joined with `*paths`.

    Example:
        from_root() -> Path("D:/MLOps/MLOps-Insurance-Project")
        from_root("logs", mkdirs=True) -> Path(".../logs") and creates it
    """
    start_dir = Path(start).resolve() if start else _caller_start_dir()
    root = _find_root(start_dir, markers)

    out = root.joinpath(*[str(p) for p in paths]) if paths else root

    if mkdirs:
        out.mkdir(parents=True, exist_ok=True)

    return out
