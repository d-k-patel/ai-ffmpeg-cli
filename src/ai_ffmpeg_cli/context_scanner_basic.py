"""Basic context scanner for ai-ffmpeg-cli.

This module provides basic file context scanning functionality,
identifying media files in the current directory for LLM context.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404: subprocess is used safely with explicit args and no shell
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .file_operations import most_recent_file

# Initialize console for Rich output
console = Console()

# Supported media file extensions for context scanning
MEDIA_EXTS = {
    "video": {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".3gp", ".flv", ".wmv"},
    "audio": {".mp3", ".aac", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".opus"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"},
    "subtitle": {".srt", ".vtt", ".ass", ".ssa", ".sub", ".idx"},
}


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _format_duration(seconds: float | None) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds is None:
        return "Unknown"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def _ffprobe_duration(path: Path) -> float | None:
    """Extract duration of a media file using ffprobe.

    Uses ffprobe to get the duration of video or audio files
    for context information.

    Args:
        path: Path to the media file

    Returns:
        Duration in seconds, or None if ffprobe is unavailable or fails
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
        # Return None for any ffprobe errors
        return None


def _display_scan_summary(context: dict) -> None:
    """Display a summary of the scan results using Rich.

    Args:
        context: Context dictionary from scan()
    """
    # Create summary table
    summary_table = Table(title="[bold blue]Scan Summary[/bold blue]", show_header=False, box=None)
    summary_table.add_column("Category", style="bold cyan")
    summary_table.add_column("Count", style="bold green", justify="center")
    summary_table.add_column("Details", style="white")

    # Add video files
    videos = context.get("videos", [])
    if videos:
        total_size = sum(Path(v).stat().st_size for v in videos if Path(v).exists())
        summary_table.add_row(
            "Videos",
            str(len(videos)),
            f"Total size: {_format_file_size(total_size)}",
        )

    # Add audio files
    audios = context.get("audios", [])
    if audios:
        total_size = sum(Path(a).stat().st_size for a in audios if Path(a).exists())
        summary_table.add_row(
            "Audio", str(len(audios)), f"Total size: {_format_file_size(total_size)}"
        )

    # Add image files
    images = context.get("images", [])
    if images:
        total_size = sum(Path(i).stat().st_size for i in images if Path(i).exists())
        summary_table.add_row(
            "Images", str(len(images)), f"Total size: {_format_file_size(total_size)}"
        )

    # Add subtitle files
    subtitle_files = context.get("subtitle_files", [])
    if subtitle_files:
        summary_table.add_row("Subtitles", str(len(subtitle_files)), "Ready for processing")

    if summary_table.row_count > 0:
        console.print(summary_table)
        console.print()


def _display_detailed_file_info(context: dict) -> None:
    """Display detailed file information in a table format.

    Args:
        context: Context dictionary from scan()
    """
    info = context.get("info", [])
    if not info:
        return

    # Create detailed file table
    file_table = Table(title="[bold green]File Details[/bold green]")
    file_table.add_column("File", style="bold white")
    file_table.add_column("Size", style="cyan", justify="right")
    file_table.add_column("Duration", style="yellow", justify="center")
    file_table.add_column("Type", style="bold", justify="center")

    for file_info in info:
        path = Path(file_info["path"])
        size = file_info.get("size", 0)
        duration = file_info.get("duration")

        # Determine file type
        ext = path.suffix.lower()
        if ext in MEDIA_EXTS["video"]:
            file_type = "Video"
        elif ext in MEDIA_EXTS["audio"]:
            file_type = "Audio"
        else:
            file_type = "Other"

        file_table.add_row(
            path.name,
            _format_file_size(size) if size else "Unknown",
            _format_duration(duration),
            file_type,
        )

    if file_table.row_count > 0:
        console.print(file_table)
        console.print()


def scan(cwd: Path | None = None, show_summary: bool = True) -> dict[str, Any]:
    """Scan current directory for media files and build context.

    Scans the specified directory (or current working directory)
    for media files and builds a context dictionary containing
    file information for LLM processing.

    Args:
        cwd: Directory to scan (defaults to current working directory)
        show_summary: Whether to display scan summary (default: True)

    Returns:
        Dictionary containing:
        - cwd: Current working directory path
        - videos: List of video file paths
        - audios: List of audio file paths
        - images: List of image file paths
        - subtitle_files: List of subtitle file paths
        - most_recent_video: Path to most recently modified video
        - info: List of file info dictionaries with path, size, and duration
    """
    base = cwd or Path.cwd()
    files: list[Path] = []
    # Scan current directory only for media files
    files.extend([p for p in base.iterdir() if p.is_file()])

    # Categorize files by media type
    videos = [p for p in files if p.suffix.lower() in MEDIA_EXTS["video"]]
    audios = [p for p in files if p.suffix.lower() in MEDIA_EXTS["audio"]]
    images = [p for p in files if p.suffix.lower() in MEDIA_EXTS["image"]]
    subtitle_files = [p for p in files if p.suffix.lower() in MEDIA_EXTS["subtitle"]]

    # Find the most recently modified video file
    most_recent_video = most_recent_file(videos)

    # Build detailed info for video and audio files
    info = []
    for p in videos + audios:
        info.append(
            {
                "path": str(p),
                "size": p.stat().st_size if p.exists() else None,
                "duration": _ffprobe_duration(p),
            }
        )

    context = {
        "cwd": str(base),
        "videos": [str(p) for p in videos],
        "audios": [str(p) for p in audios],
        "images": [str(p) for p in images],
        "subtitle_files": [str(p) for p in subtitle_files],
        "most_recent_video": str(most_recent_video) if most_recent_video else None,
        "info": info,
    }

    # Display scan summary if requested
    if show_summary:
        _display_scan_summary(context)
        _display_detailed_file_info(context)

    return context
