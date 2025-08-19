from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404: subprocess is used safely with explicit args and no shell
from pathlib import Path

from .io_utils import most_recent_file

MEDIA_EXTS = {
    "video": {".mp4", ".mov", ".mkv", ".webm", ".avi"},
    "audio": {".mp3", ".aac", ".wav", ".m4a", ".flac"},
    "image": {".png", ".jpg", ".jpeg"},
}


def _ffprobe_duration(path: Path) -> float | None:
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        return None
    try:
        # Call ffprobe via absolute path, pass filename as a separate argument, no shell
        result = subprocess.run(  # nosec B603: command is fixed and arguments are not executed via shell
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            check=True,
            text=True,
        )
        data = json.loads(result.stdout)
        dur = data.get("format", {}).get("duration")
        return float(dur) if dur is not None else None
    except Exception:
        return None


def scan(cwd: Path | None = None) -> dict[str, object]:
    base = cwd or Path.cwd()
    files: list[Path] = [p for p in base.iterdir() if p.is_file()]

    videos = [p for p in files if p.suffix.lower() in MEDIA_EXTS["video"]]
    audios = [p for p in files if p.suffix.lower() in MEDIA_EXTS["audio"]]
    images = [p for p in files if p.suffix.lower() in MEDIA_EXTS["image"]]

    most_recent_video = most_recent_file(videos)

    info = []
    for p in videos + audios:
        info.append(
            {
                "path": str(p),
                "size": p.stat().st_size if p.exists() else None,
                "duration": _ffprobe_duration(p),
            }
        )

    return {
        "cwd": str(base),
        "videos": [str(p) for p in videos],
        "audios": [str(p) for p in audios],
        "images": [str(p) for p in images],
        "most_recent_video": str(most_recent_video) if most_recent_video else None,
        "info": info,
    }
