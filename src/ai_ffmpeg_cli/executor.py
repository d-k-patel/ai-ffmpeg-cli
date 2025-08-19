from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404: subprocess used with explicit list args, no shell
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .confirm import confirm_prompt
from .errors import ExecError

logger = logging.getLogger(__name__)


def _format_command(cmd: list[str]) -> str:
    return " ".join(cmd)


def _extract_output_path(cmd: list[str]) -> Path | None:
    """Extract the output file path from an ffmpeg command."""
    if len(cmd) < 2:
        return None
    # Output file is typically the last argument in ffmpeg commands
    return Path(cmd[-1])


def _check_overwrite_protection(commands: list[list[str]], assume_yes: bool = False) -> bool:
    """Check for existing output files and prompt for overwrite confirmation."""
    existing_files = []

    for cmd in commands:
        output_path = _extract_output_path(cmd)
        if output_path and output_path.exists():
            existing_files.append(output_path)

    if not existing_files:
        return True  # No conflicts, proceed

    if assume_yes:
        return True  # Skip confirmation

    # Show which files would be overwritten
    console = Console()
    console.print(
        "\n[yellow]Warning: The following files already exist and will be overwritten:[/yellow]"
    )
    for file_path in existing_files:
        console.print(f"  • {file_path}")
    console.print()

    return confirm_prompt(
        "Continue and overwrite these files?", default_yes=False, assume_yes=assume_yes
    )


def preview(commands: list[list[str]]) -> None:
    console = Console()
    table = Table(title="Planned ffmpeg Commands")
    table.add_column("#", justify="right")
    table.add_column("Command", overflow="fold")

    for idx, cmd in enumerate(commands, start=1):
        table.add_row(str(idx), _format_command(cmd))

    console.print(table)


def run(
    commands: list[list[str]],
    confirm: bool,
    dry_run: bool,
    show_preview: bool = True,
    assume_yes: bool = False,
) -> int:
    if show_preview:
        preview(commands)
    if dry_run:
        return 0
    if not confirm:
        return 0

    # Check for overwrite conflicts before execution
    if not _check_overwrite_protection(commands, assume_yes):
        logger.info("Operation cancelled by user due to file conflicts")
        return 1

    for cmd in commands:
        # Validate executable exists to avoid PATH surprises
        if not cmd:
            raise ExecError("Empty command received for execution.")
        ffmpeg_exec = cmd[0]
        resolved = shutil.which(ffmpeg_exec)
        if resolved is None:
            raise ExecError(
                f"Executable not found: {ffmpeg_exec}. Ensure it is installed and on PATH."
            )
        try:
            result = subprocess.run(cmd, check=True)  # nosec B603: fixed binary, no shell, args vetted
            if result.returncode != 0:
                raise ExecError(
                    f"ffmpeg command failed with exit code {result.returncode}. "
                    f"Common causes: (1) input file not found or corrupted, "
                    f"(2) invalid output format or codec, "
                    f"(3) insufficient disk space, "
                    f"(4) permission issues. Check file paths and try again."
                )
        except subprocess.CalledProcessError as exc:
            logger.error("ffmpeg execution failed: %s", exc)
            raise ExecError(
                f"ffmpeg execution failed with error: {exc}. "
                f"Please verify: (1) input files exist and are readable, "
                f"(2) output directory is writable, "
                f"(3) ffmpeg is properly installed (try 'ffmpeg -version'), "
                f"(4) file formats are supported. "
                f"Use --verbose for detailed logging."
            ) from exc
    return 0
