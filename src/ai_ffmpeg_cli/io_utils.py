from __future__ import annotations

import glob
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def expand_globs(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        for match in glob.glob(pattern, recursive=True):
            paths.append(Path(match).resolve())
    unique: list[Path] = []
    seen = set()
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def is_safe_path(path: object) -> bool:
    # Guard against empty or root paths; avoid clobbering directories
    try:
        s = str(path)
    except Exception:
        return False
    return not (s.strip() == "" or s in {"/", "\\"})


def ensure_parent_dir(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def quote_path(path: Path) -> str:
    # Use simple quoting suitable for preview text; subprocess will bypass shell
    return str(path)


def most_recent_file(paths: Iterable[Path]) -> Path | None:
    latest: tuple[float, Path] | None = None
    for p in paths:
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if latest is None or mtime > latest[0]:
            latest = (mtime, p)
    return latest[1] if latest else None
