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
    """Print version and exit."""
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
    """Initialize global options and optionally run one-shot prompt."""
    setup_logging(verbose)
    try:
        cfg = load_config()
        if model:
            cfg.model = model
        if dry_run is not None:
            cfg.dry_run = dry_run
        cfg.timeout_seconds = timeout

        if ctx is not None:
            ctx.obj = {"config": cfg, "assume_yes": yes}

        # One-shot if a prompt is passed to the top-level
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
    if ctx.invoked_subcommand is None:
        # Only run natural language processing if no subcommand is invoked
        _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose)
    else:
        # Set up logging for subcommands
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
    _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose)


@app.command(name="nl")
def nl(
    ctx: typer.Context,
    prompt: str | None = typer.Argument(None, help="Natural language prompt"),
) -> None:
    """Translate NL to ffmpeg, preview, confirm, and execute."""
    if ctx.obj is None:
        # Initialize context if not already done
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
        # One-shot mode
        try:
            code = process_natural_language_prompt(prompt, config, assume_yes)
            raise typer.Exit(code)
        except Exception as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e
    else:
        # Interactive mode
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
    """Explain what an ffmpeg command does."""
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

    # Basic command parsing and explanation
    parts = ffmpeg_command.split()
    if not parts or parts[0] != "ffmpeg":
        rprint("[red]Error:[/red] Not a valid ffmpeg command. Commands should start with 'ffmpeg'.")
        raise typer.Exit(1)

    rprint("[bold]Analyzing ffmpeg command:[/bold]")
    rprint(f"  {ffmpeg_command}")
    rprint()

    # Simple explanation based on common patterns
    explanation_parts = []

    # Check for input files
    input_files = []
    for i, part in enumerate(parts):
        if part == "-i" and i + 1 < len(parts):
            input_files.append(parts[i + 1])

    if input_files:
        explanation_parts.append(f"📁 Input files: {', '.join(input_files)}")

    # Check for output file (usually the last argument)
    if len(parts) > 1:
        output_file = parts[-1]
        if not output_file.startswith("-"):
            explanation_parts.append(f"📤 Output file: {output_file}")

    # Check for common operations
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
