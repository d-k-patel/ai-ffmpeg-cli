"""Context scanner for ai-ffmpeg-cli.

This module scans the current working directory to identify available media files
and provides context information for natural language processing. It detects
videos, audio files, and images, and extracts metadata like duration and file size.

Key features:
- Media file detection by extension
- Duration extraction using ffprobe
- File size and metadata collection
- Most recent file identification
- Comprehensive context information

Supported formats:
- Video: mp4, mov, mkv, webm, avi
- Audio: mp3, aac, wav, m4a, flac
- Image: png, jpg, jpeg
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404: subprocess is used safely with explicit args and no shell
from pathlib import Path

from .io_utils import most_recent_file

# Supported media file extensions by category
MEDIA_EXTS = {
    "video": {".mp4", ".mov", ".mkv", ".webm", ".avi"},
    "audio": {".mp3", ".aac", ".wav", ".m4a", ".flac"},
    "image": {".png", ".jpg", ".jpeg"},
}


def _ffprobe_duration(path: Path) -> float | None:
    """Extract duration of media file using ffprobe.

    Uses ffprobe to get the duration of video or audio files.
    Returns None if ffprobe is not available or the file cannot be processed.

    Args:
        path: Path to the media file

    Returns:
        float | None: Duration in seconds, or None if not available

    Note:
        Requires ffprobe to be installed and available in PATH.
        Gracefully handles missing ffprobe or processing errors.
    """
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        return None
    try:
        # Call ffprobe with explicit args and no shell for security
        result = subprocess.run(  # nosec B603, B607
            [
                "ffprobe",
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
        # Return None for any ffprobe errors (file not found, invalid format, etc.)
        return None


def scan(cwd: Path | None = None) -> dict[str, object]:
    """Scan current directory for media files and extract context information.

    Analyzes the specified directory (or current working directory) to find
    media files and gather metadata. Provides comprehensive context for
    natural language processing and command generation.

    Args:
        cwd: Directory to scan (defaults to current working directory)

    Returns:
        dict: Context information containing:
            - cwd: Current working directory path
            - videos: List of video file paths
            - audios: List of audio file paths
            - images: List of image file paths
            - most_recent_video: Path to most recently modified video
            - info: Detailed metadata for videos and audio files
    """
    base = cwd or Path.cwd()
    files: list[Path] = [p for p in base.iterdir() if p.is_file()]

    # Categorize files by media type
    videos = [p for p in files if p.suffix.lower() in MEDIA_EXTS["video"]]
    audios = [p for p in files if p.suffix.lower() in MEDIA_EXTS["audio"]]
    images = [p for p in files if p.suffix.lower() in MEDIA_EXTS["image"]]

    # Find the most recently modified video file
    most_recent_video = most_recent_file(videos)

    # Collect detailed metadata for videos and audio files
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
