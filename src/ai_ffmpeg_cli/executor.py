"""Command execution utilities for ai-ffmpeg-cli.

This module handles the execution of ffmpeg commands with proper
validation, error handling, and user interaction.
"""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404: subprocess used with explicit list args, no shell
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .confirm import confirm_prompt
from .custom_exceptions import ExecError

logger = logging.getLogger(__name__)

# Initialize console for Rich output
console = Console()


def _format_command(cmd: list[str]) -> str:
    """Format command list as a readable string.

    Converts a command argument list into a space-separated string
    for display purposes.

    Args:
        cmd: Command argument list

    Returns:
        Formatted command string
    """
    return " ".join(cmd)


def _extract_output_path(cmd: list[str]) -> Path | None:
    """Extract the output file path from an ffmpeg command.

    Parses the command to find the output file path, which is
    typically the last argument in ffmpeg commands.

    Args:
        cmd: ffmpeg command argument list

    Returns:
        Output file path, or None if not found
    """
    if len(cmd) < 2:
        return None
    # Output file is typically the last argument in ffmpeg commands
    return Path(cmd[-1])


def _check_overwrite_protection(commands: list[list[str]], assume_yes: bool = False) -> bool:
    """Check for existing output files and prompt for overwrite confirmation.

    Scans all commands for existing output files and prompts the user
    for confirmation before overwriting them.

    Args:
        commands: List of ffmpeg command lists to check
        assume_yes: Whether to skip confirmation prompts

    Returns:
        True if operation should proceed, False if cancelled
    """
    existing_files = []

    # Scan all commands for existing output files
    for cmd in commands:
        output_path = _extract_output_path(cmd)
        if output_path and output_path.exists():
            existing_files.append(output_path)

    if not existing_files:
        return True  # No conflicts, proceed

    if assume_yes:
        return True  # Skip confirmation

    # Show which files would be overwritten in a table
    overwrite_table = Table(title="[bold yellow]Files That Will Be Overwritten[/bold yellow]")
    overwrite_table.add_column("#", style="bold red", justify="center")
    overwrite_table.add_column("File Path", style="white")
    overwrite_table.add_column("Size", style="cyan", justify="right")

    for i, file_path in enumerate(existing_files, 1):
        size = file_path.stat().st_size if file_path.exists() else 0
        size_str = (
            f"{size / (1024 * 1024):.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
        )
        overwrite_table.add_row(str(i), str(file_path), size_str)

    console.print(overwrite_table)
    console.print()

    return confirm_prompt(
        "Continue and overwrite these files?", default_yes=False, assume_yes=assume_yes
    )


def preview(commands: list[list[str]]) -> None:
    """Display a preview of planned ffmpeg commands.

    Shows a formatted table of all commands that will be executed,
    allowing users to review before confirmation.

    Args:
        commands: List of ffmpeg command lists to preview
    """
    if not commands:
        console.print("[yellow]⚠️ No commands to preview[/yellow]")
        return

    # Create enhanced command preview table
    table = Table(title="[bold green]Planned ffmpeg Commands[/bold green]")
    table.add_column("#", style="bold cyan", justify="center")
    table.add_column("Command", style="white", overflow="fold")
    table.add_column("Output", style="green", overflow="fold")
    table.add_column("Status", style="bold", justify="center")

    for idx, cmd in enumerate(commands, start=1):
        # Extract output file for display
        output_path = _extract_output_path(cmd)
        output_display = str(output_path) if output_path else "N/A"

        # Check if output file exists
        status = "New" if not output_path or not output_path.exists() else "Overwrite"

        table.add_row(str(idx), _format_command(cmd), output_display, status)

    console.print(table)
    console.print()


def _execute_single_command(cmd: list[str], cmd_num: int, total_cmds: int) -> None:
    """Execute a single ffmpeg command with progress feedback.

    Args:
        cmd: Command to execute
        cmd_num: Current command number (1-based)
        total_cmds: Total number of commands
    """
    # Validate command is not empty
    if not cmd:
        raise ExecError("Empty command received for execution.")

    # Validate executable exists to avoid PATH surprises
    ffmpeg_exec = cmd[0]
    resolved = shutil.which(ffmpeg_exec)
    if resolved is None:
        raise ExecError(f"Executable not found: {ffmpeg_exec}. Ensure it is installed and on PATH.")

    # Final security validation of the command
    from .file_operations import validate_ffmpeg_command

    if not validate_ffmpeg_command(cmd):
        logger.error(f"Command failed security validation: {' '.join(cmd[:3])}...")
        raise ExecError(
            "Command failed security validation. This could be due to: "
            "(1) unsafe file paths or arguments, "
            "(2) unsupported ffmpeg flags, "
            "or (3) potential security risks. "
            "Please check your input and try a simpler operation."
        )

    # Show command being executed
    output_path = _extract_output_path(cmd)
    console.print(f"[bold blue]Executing command {cmd_num}/{total_cmds}:[/bold blue]")
    console.print(f"[dim]Output:[/dim] {output_path}")

    try:
        # Execute the command with proper error handling
        result = subprocess.run(cmd, check=True)  # nosec B603: fixed binary, no shell, args vetted
        if result.returncode != 0:
            raise ExecError(
                f"ffmpeg command failed with exit code {result.returncode}. "
                f"Common causes: (1) input file not found or corrupted, "
                f"(2) invalid output format or codec, "
                f"(3) insufficient disk space, "
                f"(4) permission issues. Check file paths and try again."
            )
        console.print(f"[green]Command {cmd_num} completed successfully[/green]")
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


def run(
    commands: list[list[str]],
    confirm: bool,
    dry_run: bool,
    show_preview: bool = True,
    assume_yes: bool = False,
    output_dir: Path | None = None,
) -> int:
    """Execute ffmpeg commands with validation and error handling.

    Runs a list of ffmpeg commands with comprehensive validation,
    error handling, and user interaction. Supports dry-run mode
    for testing without actual execution.

    Args:
        commands: List of ffmpeg command lists to execute
        confirm: Whether user has confirmed execution
        dry_run: Whether to only preview without executing
        show_preview: Whether to show command preview
        assume_yes: Whether to skip confirmation prompts

    Returns:
        Exit code (0 for success, non-zero for failure)

    Raises:
        ExecError: When command execution fails or validation errors occur
    """
    if not commands:
        console.print("[yellow]⚠️ No commands to execute[/yellow]")
        return 0

    if show_preview:
        preview(commands)

    if dry_run:
        console.print("[bold yellow]Dry run mode - no commands will be executed[/bold yellow]")
        return 0

    if not confirm:
        console.print("[yellow]Execution cancelled by user[/yellow]")
        return 0

    # Check for overwrite conflicts before execution
    if not _check_overwrite_protection(commands, assume_yes):
        logger.info("Operation cancelled by user due to file conflicts")
        console.print("[yellow]Operation cancelled due to file conflicts[/yellow]")
        return 1

    # Execute commands with progress feedback
    total_commands = len(commands)
    successful_commands = 0

    console.print(
        f"\n[bold green]Starting execution of {total_commands} command(s)...[/bold green]"
    )
    console.print()

    for i, cmd in enumerate(commands, 1):
        try:
            _execute_single_command(cmd, i, total_commands)
            successful_commands += 1
        except ExecError as e:
            console.print(f"[red]Command {i} failed:[/red] {e}")
            # Re-raise any command failure
            raise

    # Show final summary
    console.print()
    if successful_commands == total_commands:
        summary_panel = Panel(
            f"[bold green]All {total_commands} commands completed successfully![/bold green]",
            title="[bold green]Execution Summary[/bold green]",
            border_style="green",
        )
        console.print(summary_panel)

        # Show completion summary with generated files
        if output_dir:
            from .main import _display_completion_summary

            _display_completion_summary(output_dir)
    else:
        summary_panel = Panel(
            f"[yellow]{successful_commands}/{total_commands} commands completed successfully[/yellow]",
            title="[bold yellow]Execution Summary[/bold yellow]",
            border_style="yellow",
        )
        console.print(summary_panel)

    return 0 if successful_commands == total_commands else 1
