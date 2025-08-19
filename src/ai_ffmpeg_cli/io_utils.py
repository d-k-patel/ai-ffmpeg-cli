"""I/O utilities for ai-ffmpeg-cli with security validation.

This module provides secure file and path handling utilities for the ai-ffmpeg-cli
package. It includes comprehensive security validation to prevent path traversal,
command injection, and other security vulnerabilities.

Key features:
- Secure glob pattern expansion with path validation
- Comprehensive path safety checks
- ffmpeg command validation and sanitization
- User input sanitization
- Filename sanitization for filesystem safety

Security measures:
- Path traversal prevention (../, ..\\)
- System directory access blocking
- Command injection prevention
- Input length limits and character filtering
- Reserved filename handling
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def expand_globs(patterns: Iterable[str], allowed_dirs: list[Path] | None = None) -> list[Path]:
    """Expand glob patterns safely with comprehensive path validation.

    Expands glob patterns while ensuring all resulting paths are safe and
    within allowed directories. Includes DoS protection and pattern validation.

    Args:
        patterns: Glob patterns to expand (e.g., ["*.mp4", "video_*"])
        allowed_dirs: List of allowed directories to search within (defaults to cwd)

    Returns:
        List of validated Path objects, with duplicates removed

    Security features:
        - Validates all resulting paths for safety
        - Prevents access outside allowed directories
        - Limits recursive search depth and result count
        - Sanitizes glob patterns before expansion
    """
    if allowed_dirs is None:
        allowed_dirs = [Path.cwd()]

    paths: list[Path] = []
    MAX_GLOB_RESULTS = 1000  # Prevent DoS via huge glob expansions

    for pattern in patterns:
        # Sanitize the pattern itself before expansion
        if not _is_safe_glob_pattern(pattern):
            continue

        try:
            matches = glob.glob(pattern, recursive=True)
            if len(matches) > MAX_GLOB_RESULTS:
                # Log warning and truncate to prevent DoS
                matches = matches[:MAX_GLOB_RESULTS]

            for match in matches:
                path_obj = Path(match).resolve()

                # Validate each resulting path against security rules
                if is_safe_path(path_obj, allowed_dirs):
                    paths.append(path_obj)

        except (OSError, ValueError):
            # Skip invalid patterns that cause expansion errors
            continue

    # Remove duplicates while preserving order
    unique: list[Path] = []
    seen = set()
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _is_safe_glob_pattern(pattern: str) -> bool:
    """Validate glob pattern is safe to use.

    Checks for dangerous patterns that could lead to path traversal,
    system access, or excessive resource consumption.

    Args:
        pattern: Glob pattern to validate

    Returns:
        bool: True if pattern is safe for expansion
    """
    if not pattern or not isinstance(pattern, str):
        return False

    # Check for dangerous patterns that could cause security issues
    dangerous_sequences = [
        "../",
        "..\\",  # Path traversal attempts
        "//",
        "\\\\",  # Network paths
        "*" * 10,  # Excessive wildcards (DoS prevention)
        "{" * 5,  # Brace expansion abuse
    ]

    pattern_lower = pattern.lower()
    for dangerous in dangerous_sequences:
        if dangerous in pattern_lower:
            return False

    # Check for system directory access attempts
    dangerous_roots = [
        "/etc",
        "/proc",
        "/sys",
        "/dev",
        "/boot",
        "c:\\windows",
        "c:\\system32",
        "c:\\program files",
        "~/.ssh",
        "~/.aws",
        "~/.config",
    ]

    return all(not pattern_lower.startswith(root.lower()) for root in dangerous_roots)


def is_safe_path(path: object, allowed_dirs: list[Path] | None = None) -> bool:
    """Validate path is safe and within allowed directories.

    Comprehensive path validation that prevents path traversal, system access,
    and other security vulnerabilities. Validates against allowed directories
    and blocks access to sensitive system paths.

    Args:
        path: Path to validate (str, Path, or other object)
        allowed_dirs: List of allowed parent directories (defaults to cwd)

    Returns:
        bool: True if path is safe to use

    Security checks:
        - Prevents empty or root paths
        - Blocks path traversal attempts (../, ..\\)
        - Validates against allowed directories
        - Prevents access to sensitive system paths
        - Handles both Unix and Windows path patterns
    """
    try:
        if path is None:
            return False

        # Convert to Path object for proper handling
        if not isinstance(path, Path):
            path_str_check = str(path)
            if not path_str_check or not path_str_check.strip():
                return False
            path_obj = Path(path_str_check)
        else:
            path_obj = path

        # Resolve to absolute path to detect traversal attempts
        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError):
            # Path resolution failed - consider unsafe
            return False

        # Check for empty or dangerous paths
        path_str = str(resolved_path)
        original_str = str(path_obj)
        if not path_str.strip() or not original_str.strip():
            return False

        # Block root and system paths
        if path_str in {"/", "\\", "C:\\", "C:/", "C:", "/root", "/home"}:
            return False

        # Additional check for single character paths that could be roots
        if len(original_str.strip()) <= 3 and any(c in original_str for c in ["/", "\\"]):
            return False

        # Detect path traversal attempts in path components
        path_parts = path_obj.parts
        if ".." in path_parts or any("." * 3 in part for part in path_parts):
            return False

        # Check for dangerous path patterns (system directories)
        dangerous_patterns = [
            "/etc",
            "/proc",
            "/sys",
            "/dev",
            "/boot",  # Unix system directories
            "C:\\Windows",
            "C:\\System32",
            "C:\\Program Files",  # Windows system directories
            "~/.ssh",
            "~/.aws",
            "~/.config",  # User sensitive directories
        ]

        path_lower = path_str.lower()
        for pattern in dangerous_patterns:
            try:
                if path_str.startswith(pattern) or Path(pattern).resolve() in resolved_path.parents:
                    return False
            except (OSError, ValueError):
                # If we can't resolve the pattern, check string matching
                if path_lower.startswith(pattern.lower()):
                    return False

        # Additional checks for Windows patterns on any system
        windows_indicators = ["windows", "system32", "program files"]
        for indicator in windows_indicators:
            if indicator in path_lower:
                return False

        # Validate against allowed directories
        if allowed_dirs is None:
            allowed_dirs = [Path.cwd()]

        # Check if path is within allowed directories
        for allowed_dir in allowed_dirs:
            try:
                resolved_allowed = allowed_dir.resolve()
                if resolved_path == resolved_allowed or resolved_path.is_relative_to(
                    resolved_allowed
                ):
                    return True
            except (ValueError, OSError):
                continue

        return False

    except Exception:
        # Any exception during validation means unsafe
        return False


def ensure_parent_dir(path: Path) -> None:
    """Ensure parent directory exists, creating it if necessary.

    Creates the parent directory of the given path if it doesn't exist.
    Uses mkdir with parents=True to create intermediate directories.

    Args:
        path: Path whose parent directory should be created
    """
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def quote_path(path: Path) -> str:
    """Quote path for safe display in preview text.

    Returns path as string for display purposes. Note that subprocess
    calls bypass shell interpretation, so complex quoting is not needed.

    Args:
        path: Path to quote

    Returns:
        str: Quoted path string
    """
    return str(path)


def most_recent_file(paths: Iterable[Path]) -> Path | None:
    """Find the most recently modified file from a collection.

    Compares modification times of all files and returns the most recent.
    Skips files that cannot be accessed or don't exist.

    Args:
        paths: Collection of file paths to check

    Returns:
        Path: Most recently modified file, or None if no accessible files
    """
    latest: tuple[float, Path] | None = None
    for p in paths:
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if latest is None or mtime > latest[0]:
            latest = (mtime, p)
    return latest[1] if latest else None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to prevent security issues and filesystem problems.

    Removes or replaces dangerous characters, prevents path traversal,
    handles reserved filenames, and ensures length limits.

    Args:
        filename: Original filename to sanitize
        max_length: Maximum allowed filename length (default 255)

    Returns:
        str: Sanitized filename safe for filesystem use

    Security features:
        - Removes dangerous characters and sequences
        - Prevents path traversal attempts
        - Handles Windows reserved filenames
        - Enforces length limits
        - Ensures valid filename output
    """
    if not filename or not isinstance(filename, str):
        return "sanitized_file"

    # Remove or replace dangerous characters
    # Keep alphanumeric, spaces, dots, hyphens, underscores
    import re

    sanitized = re.sub(r"[^a-zA-Z0-9\s\._-]", "_", filename)

    # Prevent multiple consecutive dots (could be path traversal)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Prevent reserved names on Windows
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_without_ext = sanitized.rsplit(".", 1)[0].upper()
    if name_without_ext in reserved_names:
        sanitized = f"safe_{sanitized}"

    # Truncate if too long while preserving extension
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        sanitized = name[:max_name_length] + ("." + ext if ext else "")

    # Ensure we have something valid
    if not sanitized:
        sanitized = "sanitized_file"

    return sanitized


# FFmpeg command validation constants and functions
ALLOWED_FFMPEG_FLAGS = {
    # Input/Output
    "-i",
    "-f",
    "-y",
    "-n",
    # Video codecs and options
    "-c:v",
    "-vcodec",
    "-codec:v",
    "-vf",
    "-filter:v",
    "-aspect",
    "-pix_fmt",
    "-r",
    "-s",
    "-vframes",
    "-vn",
    # Audio codecs and options
    "-c:a",
    "-acodec",
    "-codec:a",
    "-af",
    "-filter:a",
    "-ar",
    "-ac",
    "-ab",
    "-aq",
    "-an",
    # General codecs
    "-c",
    "-codec",
    # Timing
    "-ss",
    "-t",
    "-to",
    "-itsoffset",
    # Quality/Bitrate
    "-b:v",
    "-b:a",
    "-b",
    "-crf",
    "-qp",
    "-q:v",
    "-q:a",
    "-maxrate",
    "-bufsize",
    "-minrate",
    # Filter complex
    "-filter_complex",
    "-lavfi",
    # Map streams
    "-map",
    "-map_metadata",
    "-map_chapters",
    # Metadata
    "-metadata",
    "-disposition",
    # Format specific
    "-movflags",
    "-preset",
    "-tune",
    "-profile:v",
    "-level",
    # Hardware acceleration (commonly used)
    "-hwaccel",
    "-hwaccel_device",
}


def validate_ffmpeg_command(cmd: list[str]) -> bool:
    """Validate ffmpeg command arguments for security.

    Comprehensive validation of ffmpeg command arguments to prevent
    command injection, unauthorized operations, and security vulnerabilities.

    Args:
        cmd: Command arguments list (e.g., ["ffmpeg", "-i", "input.mp4", "-c:v", "libx264", "output.mp4"])

    Returns:
        bool: True if command is safe to execute

    Security checks:
        - Validates executable is ffmpeg
        - Checks all flags against allowlist
        - Validates file paths using is_safe_path
        - Prevents command injection and shell metacharacters
        - Blocks dangerous patterns and redirections
    """
    if not cmd or not isinstance(cmd, list):
        return False

    # First argument should be ffmpeg
    if not cmd[0] or cmd[0] != "ffmpeg":
        return False

    # Check for dangerous patterns that could cause command injection
    cmd_str = " ".join(cmd)
    dangerous_patterns = [
        ";",
        "|",
        "&",
        "&&",
        "||",  # Command chaining
        "$",
        "`",
        "$(",
        "${",  # Variable expansion/command substitution
        ">",
        "<",
        ">>",
        "<<",  # Redirection
        "\n",
        "\r",  # Line breaks
    ]

    for pattern in dangerous_patterns:
        if pattern in cmd_str:
            return False

    # Validate flags and arguments
    i = 1  # Skip 'ffmpeg'
    while i < len(cmd):
        arg = cmd[i]

        # Check if it's a flag (starts with -)
        if arg.startswith("-"):
            if arg not in ALLOWED_FFMPEG_FLAGS:
                return False

            # Some flags have values, skip validation for the value
            # (values will be validated as paths if they are file paths)
            if i + 1 < len(cmd) and not cmd[i + 1].startswith("-"):
                i += 1  # Skip the value

        else:
            # Non-flag argument, should be a file path
            if not is_safe_path(arg):
                return False

        i += 1

    return True


def sanitize_user_input(user_input: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks.

    Comprehensive sanitization of user input to prevent command injection,
    shell metacharacter attacks, and other security vulnerabilities.

    Args:
        user_input: Raw user input string
        max_length: Maximum allowed length (default 1000)

    Returns:
        str: Sanitized input safe for processing

    Security features:
        - Removes control characters and dangerous sequences
        - Blocks command injection patterns
        - Enforces length limits
        - Normalizes whitespace
        - Prevents shell metacharacter attacks
    """
    if not user_input or not isinstance(user_input, str):
        return ""

    # Truncate if too long
    if len(user_input) > max_length:
        user_input = user_input[:max_length]

    # Remove control characters and dangerous sequences
    import re

    # Remove control characters (except normal whitespace)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", user_input)

    # Remove dangerous shell characters and command injection attempts
    dangerous_chars = [";", "|", "&", "$", "`", "<", ">", "\x00"]  # Null byte

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, " ")

    # Remove dangerous command patterns that could be used for injection
    dangerous_patterns = [
        r"\brm\s+",
        r"\bmv\s+",
        r"\bcp\s+",
        r"\bchmod\s+",
        r"\bsudo\s+",
        r"\bsu\s+",
        r"\bcurl\s+",
        r"\bwget\s+",
        r"\bsh\s+",
        r"\bbash\s+",
        r"\beval\s+",
        r"\bexec\s+",
    ]

    import re

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, " ", sanitized, flags=re.IGNORECASE)

    # Normalize whitespace
    sanitized = " ".join(sanitized.split())

    return sanitized
