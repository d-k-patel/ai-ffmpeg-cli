"""Main CLI entry point for ai-ffmpeg-cli.

This module provides the command-line interface for the AI-powered ffmpeg CLI tool.
It handles both one-shot natural language processing and interactive sessions.

Key features:
- Natural language to ffmpeg command translation
- Interactive command processing with confirmation
- Basic ffmpeg command explanation
- Configuration management and error handling

Dependencies:
- typer: CLI framework
- rich: Enhanced terminal output
"""

from __future__ import annotations

import typer
from rich import print as rprint

from .cli_operations import process_interactive_session
from .cli_operations import process_natural_language_prompt
from .cli_operations import setup_logging
from .config import load_config
from .errors import BuildError
from .errors import ConfigError
from .errors import ExecError
from .errors import ParseError
from .version import __version__

app = typer.Typer(add_completion=False, help="AI-powered ffmpeg CLI")


def version_callback(value: bool) -> None:
    """Print version and exit.

    Args:
        value: Whether version flag was provided (unused, handled by typer)

    Raises:
        typer.Exit: Always raised to exit after version display
    """
    if value:
        rprint(f"aiclip version {__version__}")
        raise typer.Exit()


def _main_impl(
    ctx: typer.Context | None,
    prompt: str | None,
    yes: bool,
    model: str | None,
    dry_run: bool | None,
    timeout: int,
    verbose: bool,
) -> None:
    """Initialize global options and optionally run one-shot prompt.

    This is the core implementation function that handles both one-shot
    and interactive modes. It sets up logging, loads configuration,
    and processes natural language prompts.

    Args:
        ctx: Typer context object for subcommand handling
        prompt: Natural language prompt for one-shot processing
        yes: Whether to skip confirmation prompts
        model: LLM model override for configuration
        dry_run: Whether to preview commands without execution
        timeout: LLM request timeout in seconds
        verbose: Whether to enable verbose logging

    Raises:
        typer.Exit: On successful completion or error conditions
        ConfigError: If configuration loading fails
        ParseError: If natural language parsing fails
        BuildError: If ffmpeg command building fails
        ExecError: If command execution fails
    """
    setup_logging(verbose)
    try:
        cfg = load_config()
        # Apply command-line overrides to configuration
        if model:
            cfg.model = model
        if dry_run is not None:
            cfg.dry_run = dry_run
        cfg.timeout_seconds = timeout

        if ctx is not None:
            ctx.obj = {"config": cfg, "assume_yes": yes}

        # One-shot mode: process single prompt and exit
        if prompt is not None:
            try:
                code = process_natural_language_prompt(prompt, cfg, yes)
                raise typer.Exit(code)
            except (ParseError, BuildError, ExecError) as e:
                rprint(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from e
    except ConfigError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.callback(invoke_without_command=True)
def cli_main(
    ctx: typer.Context,
    prompt: str | None = typer.Argument(
        None, help="Natural language prompt; if provided, runs once and exits"
    ),
    yes: bool = typer.Option(False, "--yes/--no-yes", help="Skip confirmation and overwrite"),
    model: str | None = typer.Option(None, "--model", help="LLM model override"),
    dry_run: bool = typer.Option(None, "--dry-run/--no-dry-run", help="Preview only"),
    timeout: int = typer.Option(60, "--timeout", help="LLM timeout seconds"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
    _version: bool = typer.Option(
        False, "--version", callback=version_callback, help="Show version and exit"
    ),
) -> None:
    """Main CLI entry point with global options.

    Handles both direct invocation (one-shot mode) and subcommand routing.
    When invoked without subcommands, processes natural language prompts.
    When subcommands are used, sets up logging for subcommand execution.

    Args:
        ctx: Typer context for command routing
        prompt: Optional natural language prompt for one-shot processing
        yes: Skip confirmation prompts and overwrite files
        model: Override default LLM model
        dry_run: Preview commands without execution
        timeout: LLM request timeout in seconds
        verbose: Enable verbose logging output
        _version: Version flag (handled by callback)
    """
    if ctx.invoked_subcommand is None:
        # Direct invocation: run natural language processing
        _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose)
    else:
        # Subcommand mode: set up logging for subcommand execution
        setup_logging(verbose)


def main(
    ctx: typer.Context | None = None,
    prompt: str | None = None,
    yes: bool = False,
    model: str | None = None,
    dry_run: bool | None = None,
    timeout: int = 60,
    verbose: bool = False,
) -> None:
    """Programmatic entry point for testing and library usage.

    Provides the same functionality as CLI but with direct parameter passing.
    Useful for testing, scripting, and programmatic integration.

    Args:
        ctx: Optional typer context (for subcommand compatibility)
        prompt: Natural language prompt to process
        yes: Skip confirmation prompts
        model: LLM model override
        dry_run: Preview mode without execution
        timeout: LLM timeout in seconds
        verbose: Enable verbose logging
    """
    _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose)


@app.command(name="nl")
def nl(
    ctx: typer.Context,
    prompt: str | None = typer.Argument(None, help="Natural language prompt"),
) -> None:
    """Translate NL to ffmpeg, preview, confirm, and execute.

    This subcommand provides natural language to ffmpeg command translation.
    It can run in one-shot mode (with prompt argument) or interactive mode.

    Args:
        ctx: Typer context containing configuration
        prompt: Natural language prompt for one-shot processing

    Raises:
        typer.Exit: On completion or error conditions
    """
    if ctx.obj is None:
        # Initialize context if not already done by main callback
        setup_logging(False)
        try:
            cfg = load_config()
            ctx.obj = {"config": cfg, "assume_yes": False}
        except ConfigError as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e

    config = ctx.obj["config"]
    assume_yes = ctx.obj["assume_yes"]

    if prompt is not None:
        # One-shot mode: process single prompt and exit
        try:
            code = process_natural_language_prompt(prompt, config, assume_yes)
            raise typer.Exit(code)
        except Exception as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e
    else:
        # Interactive mode: start interactive session
        try:
            code = process_interactive_session(config, assume_yes)
            raise typer.Exit(code)
        except Exception as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e


@app.command(name="explain-cmd")
def explain_cmd(
    ctx: typer.Context,
) -> None:
    """Explain what an ffmpeg command does.

    Provides a basic explanation of ffmpeg commands by parsing common
    patterns and flags. This is a lightweight alternative to the AI-powered
    explanation available in the 'nl' command.

    Args:
        ctx: Typer context containing command arguments

    Raises:
        typer.Exit: On completion or error conditions
    """
    # Get the remaining arguments as the ffmpeg command
    if not ctx.args:
        rprint("Provide an ffmpeg command to explain.")
        rprint("Usage: aiclip explain-cmd 'ffmpeg -i input.mp4 -c:v libx264 output.mp4'")
        raise typer.Exit(2)

    ffmpeg_command = " ".join(ctx.args)

    if not ffmpeg_command:
        rprint("Provide an ffmpeg command to explain.")
        rprint("Usage: aiclip explain-cmd 'ffmpeg -i input.mp4 -c:v libx264 output.mp4'")
        raise typer.Exit(2)

    # Basic command validation - must start with 'ffmpeg'
    parts = ffmpeg_command.split()
    if not parts or parts[0] != "ffmpeg":
        rprint("[red]Error:[/red] Not a valid ffmpeg command. Commands should start with 'ffmpeg'.")
        raise typer.Exit(1)

    rprint("[bold]Analyzing ffmpeg command:[/bold]")
    rprint(f"  {ffmpeg_command}")
    rprint()

    # Simple explanation based on common patterns
    explanation_parts = []

    # Extract input files (arguments following -i flags)
    input_files = []
    for i, part in enumerate(parts):
        if part == "-i" and i + 1 < len(parts):
            input_files.append(parts[i + 1])

    if input_files:
        explanation_parts.append(f"📁 Input files: {', '.join(input_files)}")

    # Extract output file (usually the last non-flag argument)
    if len(parts) > 1:
        output_file = parts[-1]
        if not output_file.startswith("-"):
            explanation_parts.append(f"📤 Output file: {output_file}")

    # Identify common operations based on flags and filters
    if "-vf" in ffmpeg_command or "-filter:v" in ffmpeg_command:
        explanation_parts.append("🎬 Video filtering applied")

    if "-c:v" in ffmpeg_command:
        explanation_parts.append("🎥 Video codec specified")

    if "-c:a" in ffmpeg_command:
        explanation_parts.append("🔊 Audio codec specified")

    if "-ss" in ffmpeg_command:
        explanation_parts.append("⏱️  Seeking to specific time")

    if "-t" in ffmpeg_command or "-to" in ffmpeg_command:
        explanation_parts.append("⏱️  Duration/time limit specified")

    if "-scale" in ffmpeg_command or "scale=" in ffmpeg_command:
        explanation_parts.append("📏 Video scaling/resizing")

    if "-crf" in ffmpeg_command:
        explanation_parts.append("🎯 Quality-based encoding (CRF)")

    if "-b:v" in ffmpeg_command:
        explanation_parts.append("📊 Bitrate-based encoding")

    if explanation_parts:
        rprint("[bold]What this command does:[/bold]")
        for part in explanation_parts:
            rprint(f"  {part}")
    else:
        rprint("ℹ️  Basic ffmpeg command - converts/processes media files")

    rprint()
    rprint(
        "[yellow]Note:[/yellow] This is a basic explanation. For detailed analysis, consider using the AI-powered 'nl' command."
    )


if __name__ == "__main__":
    app()
