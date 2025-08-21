"""Main entry point for the ai-ffmpeg-cli application.

This module provides the CLI interface using Typer, handling both one-shot
commands and interactive mode for natural language to ffmpeg command conversion.
"""

from __future__ import annotations

import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .command_builder import build_commands
from .config import AppConfig
from .config import load_config
from .confirm import confirm_prompt
from .context_scanner_basic import scan
from .custom_exceptions import BuildError
from .custom_exceptions import ConfigError
from .custom_exceptions import ExecError
from .custom_exceptions import ParseError
from .intent_router import route_intent
from .llm_client import LLMClient
from .llm_client import OpenAIProvider
from .version_info import __version__

# Initialize console for Rich output
console = Console()

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Typer app with completion disabled and support for invocation without subcommands
app = typer.Typer(add_completion=False, help="AI-powered ffmpeg CLI", invoke_without_command=True)


def _display_welcome_screen() -> None:
    """Display a beautiful welcome screen for the interactive mode."""
    # Create welcome panel
    welcome_text = Text()
    welcome_text.append("ai-ffmpeg-cli", style="bold white")
    welcome_text.append(" v", style="dim")
    welcome_text.append(__version__, style="bold green")
    welcome_text.append("\n\n", style="dim")
    welcome_text.append(
        "AI-powered video and audio processing with natural language", style="italic"
    )
    welcome_text.append("\n", style="dim")
    welcome_text.append(
        "Type your request in plain English and let AI handle the ffmpeg complexity!",
        style="dim",
    )

    welcome_panel = Panel(
        welcome_text,
        title="[bold cyan]Welcome to Interactive Mode[/bold cyan]",
        border_style="blue",
        padding=(1, 2),
    )

    console.print(welcome_panel)
    console.print()


def _display_system_info() -> None:
    """Display system information in a table format."""
    table = Table(title="[bold cyan]System Information[/bold cyan]", show_header=False, box=None)
    table.add_column("Property", style="bold blue")
    table.add_column("Value", style="white")

    table.add_row(
        "Python Version",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row("Platform", platform.platform())
    table.add_row("CLI Version", __version__)
    table.add_row("Start Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table)
    console.print()


def _display_context_info(context: dict, output_dir: Path | None = None) -> None:
    """Display context information in a beautiful table format."""
    if not context:
        return

    # Create context table
    table = Table(title="[bold green]Available Media Files[/bold green]", show_header=True)
    table.add_column("Type", style="bold cyan", justify="center")
    table.add_column("Count", style="bold green", justify="center")
    table.add_column("Files", style="white")

    # Add video files
    videos = context.get("videos", [])
    if videos:
        video_files = "\n".join([f"• {Path(v).name}" for v in videos[:5]])  # Show first 5
        if len(videos) > 5:
            video_files += f"\n• ... and {len(videos) - 5} more"
        table.add_row("Videos", str(len(videos)), video_files)

    # Add audio files
    audios = context.get("audios", [])
    if audios:
        audio_files = "\n".join([f"• {Path(a).name}" for a in audios[:5]])  # Show first 5
        if len(audios) > 5:
            audio_files += f"\n• ... and {len(audios) - 5} more"
        table.add_row("Audio", str(len(audios)), audio_files)

    # Add image files
    images = context.get("images", [])
    if images:
        image_files = "\n".join([f"• {Path(i).name}" for i in images[:5]])  # Show first 5
        if len(images) > 5:
            image_files += f"\n• ... and {len(images) - 5} more"
        table.add_row("Images", str(len(images)), image_files)

    # Show most recent video if available
    most_recent = context.get("most_recent_video")
    if most_recent:
        table.add_row("Recent", "1", f"• {Path(most_recent).name}")

    if table.row_count > 0:
        console.print(table)
        console.print()

    # Show output directory information if provided
    if output_dir:
        output_info = Panel(
            f"[bold]Output Directory:[/bold] {output_dir}\n"
            f"[dim]Generated files will be saved here[/dim]",
            title="[bold blue]Output Configuration[/bold blue]",
            border_style="blue",
        )
        console.print(output_info)
        console.print()


def _display_completion_summary(output_dir: Path | None = None) -> None:
    """Display a summary of available media files after completion."""
    if not output_dir:
        return

    try:
        # Scan the output directory for new media files
        from .context_scanner_basic import scan

        # Create a temporary context for the output directory
        output_context = scan(cwd=output_dir, show_summary=False)

        if not output_context:
            return

        # Create completion summary table
        completion_table = Table(
            title="[bold green]Generated Output Files[/bold green]", show_header=True
        )
        completion_table.add_column("Type", style="bold cyan", justify="center")
        completion_table.add_column("Count", style="bold green", justify="center")
        completion_table.add_column("Files", style="white")

        # Add generated video files
        videos = output_context.get("videos", [])
        if videos and isinstance(videos, list):
            video_files = "\n".join([f"• {Path(str(v)).name}" for v in videos[:5]])
            if len(videos) > 5:
                video_files += f"\n• ... and {len(videos) - 5} more"
            completion_table.add_row("Videos", str(len(videos)), video_files)

        # Add generated audio files
        audios = output_context.get("audios", [])
        if audios and isinstance(audios, list):
            audio_files = "\n".join([f"• {Path(str(a)).name}" for a in audios[:5]])
            if len(audios) > 5:
                audio_files += f"\n• ... and {len(audios) - 5} more"
            completion_table.add_row("Audio", str(len(audios)), audio_files)

        # Add generated image files
        images = output_context.get("images", [])
        if images and isinstance(images, list):
            image_files = "\n".join([f"• {Path(str(i)).name}" for i in images[:5]])
            if len(images) > 5:
                image_files += f"\n• ... and {len(images) - 5} more"
            completion_table.add_row("Images", str(len(images)), image_files)

        if completion_table.row_count > 0:
            console.print(completion_table)
            console.print()

    except (OSError, PermissionError, FileNotFoundError) as e:
        # Handle expected file system errors in completion summary
        # These are non-critical for the main application flow
        logger.debug(f"Could not display completion summary: {e}")
    except Exception as e:
        # Log unexpected errors but don't fail the application
        logger.warning(f"Unexpected error in completion summary: {e}")


def _display_config_status(cfg: AppConfig) -> None:
    """Display configuration status in a table format."""
    table = Table(
        title="[bold yellow]Configuration Status[/bold yellow]",
        show_header=False,
        box=None,
    )
    table.add_column("Setting", style="bold blue")
    table.add_column("Value", style="white")

    # Model information
    table.add_row("AI Model", cfg.model)

    # API key status
    api_key_status = "Configured" if cfg.openai_api_key else "Not configured"
    table.add_row("API Key", api_key_status)

    # Other settings
    table.add_row("Timeout", f"{cfg.timeout_seconds}s")
    table.add_row("Dry Run", "Enabled" if cfg.dry_run else "Disabled")
    table.add_row("Confirm Default", "Yes" if cfg.confirm_default else "No")

    console.print(table)
    console.print()


def _display_help_tips() -> None:
    """Display helpful tips for users."""
    tips = [
        "Try: 'convert video.mp4 to webm format'",
        "Try: 'extract audio from video.mp4'",
        "Try: 'resize video to 720p'",
        "Try: 'add subtitles to video.mp4'",
        "Type 'exit' or 'quit' to leave interactive mode",
        "Use Ctrl+C to cancel any operation",
    ]

    tip_text = Text()
    tip_text.append("Quick Tips:", style="bold white")
    tip_text.append("\n", style="dim")

    for tip in tips:
        tip_text.append(f"  {tip}\n", style="dim")

    tip_panel = Panel(
        tip_text,
        title="[bold yellow]Quick Tips[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )

    console.print(tip_panel)
    console.print()


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Sets up Rich-based logging configuration with appropriate level and format
    for the application.

    Args:
        verbose: If True, enables DEBUG level logging; otherwise uses INFO level
    """
    from .logging_config.config import log_startup_info
    from .logging_config.config import setup_logging as setup_rich_logging

    level = logging.DEBUG if verbose else logging.INFO
    setup_rich_logging(level=level, console_instance=console)
    log_startup_info()


def _main_impl(
    ctx: typer.Context | None,
    prompt: str | None,
    yes: bool,
    model: str | None,
    dry_run: bool | None,
    timeout: int,
    verbose: bool,
    output_dir: str | None,
) -> None:
    """Initialize global options and optionally run one-shot prompt.

    Core implementation function that handles configuration loading,
    context setup, and either executes a one-shot command or enters
    interactive mode.

    Args:
        ctx: Typer context object (may be None for programmatic calls)
        prompt: Natural language prompt for one-shot execution
        yes: Whether to skip confirmation prompts
        model: LLM model override
        dry_run: Whether to only preview commands without execution
        timeout: LLM timeout in seconds
        verbose: Whether to enable verbose logging

    Raises:
        typer.Exit: On successful completion or error conditions
        ConfigError: When configuration loading fails
    """
    _setup_logging(verbose)
    try:
        # Load and validate configuration
        cfg = load_config()
        if model:
            cfg.model = model
        if dry_run is not None:
            cfg.dry_run = dry_run
        if output_dir:
            cfg.output_directory = output_dir
        cfg.timeout_seconds = timeout

        # Store configuration in context for subcommands
        if ctx is not None:
            ctx.obj = {"config": cfg, "assume_yes": yes}

        # Determine if this is a one-shot invocation (no subcommand specified)
        invoked_none = (ctx is None) or (ctx.invoked_subcommand is None)
        if invoked_none:
            if prompt is not None:
                try:
                    # Execute one-shot command: scan context, parse intent, build and execute
                    context = scan(show_summary=False)  # Don't show summary for one-shot commands
                    client = _make_llm(cfg)
                    intent = client.parse(prompt, context, timeout=cfg.timeout_seconds)
                    plan = route_intent(intent, output_dir=Path(cfg.output_directory))
                    commands = build_commands(plan, assume_yes=yes)
                    from .executor import preview
                    from .executor import run

                    # Always show preview before asking for confirmation
                    preview(commands)
                    confirmed = (
                        True
                        if yes
                        else confirm_prompt("Run these commands?", cfg.confirm_default, yes)
                    )
                    code = run(
                        commands,
                        confirm=confirmed,
                        dry_run=cfg.dry_run,
                        show_preview=False,
                        assume_yes=yes,
                        output_dir=Path(cfg.output_directory),
                    )
                    raise typer.Exit(code)
                except (ParseError, BuildError, ExecError) as e:
                    console.print(f"[red]❌ Error:[/red] {e}")
                    raise typer.Exit(1) from e
            else:
                # No subcommand and no prompt: enter interactive mode
                if ctx is not None:
                    nl(ctx=ctx, prompt=None)
                return
    except ConfigError as e:
        console.print(f"[red]❌ Configuration Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.callback()
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
    output_dir: str | None = typer.Option(
        None, "--output-dir", help="Output directory for generated files"
    ),
) -> None:
    """Main CLI entry point with global options.

    Handles the top-level command line interface, setting up global options
    and delegating to the main implementation.
    """
    _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose, output_dir)


def main(
    ctx: typer.Context | None = None,
    prompt: str | None = None,
    yes: bool = False,
    model: str | None = None,
    dry_run: bool | None = None,
    timeout: int = 60,
    verbose: bool = False,
    output_dir: str | None = None,
) -> None:
    """Programmatic entry point for the application.

    Allows the application to be used programmatically without CLI arguments.
    Useful for testing and integration scenarios.

    Args:
        ctx: Optional Typer context
        prompt: Natural language prompt
        yes: Skip confirmation prompts
        model: LLM model override
        dry_run: Preview only mode
        timeout: LLM timeout in seconds
        verbose: Enable verbose logging
    """
    _main_impl(ctx, prompt, yes, model, dry_run, timeout, verbose, output_dir)


def _make_llm(cfg: AppConfig) -> LLMClient:
    """Create LLM client with secure API key handling.

    Initializes the LLM client with proper API key validation and
    provider configuration.

    Args:
        cfg: Application configuration containing API key and model settings

    Returns:
        Configured LLM client instance

    Raises:
        ConfigError: When API key is invalid or missing
    """
    try:
        # This will validate the API key format and presence
        api_key = cfg.get_api_key_for_client()
        provider = OpenAIProvider(api_key=api_key, model=cfg.model)
        return LLMClient(provider)
    except ConfigError:
        # Re-raise config errors for proper error handling
        raise


@app.command()
def nl(
    ctx: typer.Context,
    prompt: str | None = typer.Argument(None, help="Natural language prompt"),
) -> None:
    """Translate NL to ffmpeg, preview, confirm, and execute.

    Core command that handles natural language to ffmpeg command conversion.
    Supports both single command execution and interactive mode.

    Args:
        ctx: Typer context containing configuration
        prompt: Optional natural language prompt for single execution

    Raises:
        typer.Exit: On completion or error conditions
    """
    obj = ctx.obj or {}
    cfg: AppConfig = obj["config"]
    assume_yes: bool = obj["assume_yes"]

    try:
        # Initialize context and LLM client
        context = scan(
            show_summary=False
        )  # Don't show summary in interactive mode as it's shown separately
        client = _make_llm(cfg)

        def handle_one(p: str) -> int:
            """Process a single natural language prompt.

            Parses the prompt, builds commands, shows preview, and executes
            if confirmed.

            Args:
                p: Natural language prompt to process

            Returns:
                Exit code from command execution
            """
            intent = client.parse(p, context, timeout=cfg.timeout_seconds)
            plan = route_intent(intent, output_dir=Path(cfg.output_directory))
            commands = build_commands(plan, assume_yes=assume_yes)

            # Always show preview before asking for confirmation
            from .executor import preview

            preview(commands)

            confirmed = (
                True
                if assume_yes
                else confirm_prompt("Run these commands?", cfg.confirm_default, assume_yes)
            )
            return_code = 0
            if confirmed:
                from .executor import run

                return_code = run(
                    commands,
                    confirm=True,
                    dry_run=cfg.dry_run,
                    show_preview=False,
                    assume_yes=assume_yes,
                    output_dir=Path(cfg.output_directory),
                )
            return return_code

        if prompt:
            # Single command execution
            code = handle_one(prompt)
            raise typer.Exit(code)
        else:
            # Interactive mode with enhanced UI
            _display_welcome_screen()
            _display_system_info()
            _display_context_info(context, Path(cfg.output_directory))
            _display_config_status(cfg)
            _display_help_tips()

            console.print("[bold cyan]Ready for your commands![/bold cyan]")
            console.print()

            while True:
                try:
                    line = console.input("[bold green]aiclip>[/bold green] ").strip()
                except EOFError:
                    # Handle Ctrl+D gracefully
                    console.print("\n[yellow]Goodbye![/yellow]")
                    break
                if not line or line.lower() in {"exit", "quit"}:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                try:
                    handle_one(line)
                except (ParseError, BuildError, ExecError) as e:
                    console.print(f"[red]❌ Error:[/red] {e}")
    except (ConfigError, ParseError, BuildError, ExecError) as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1) from e


# Stretch goal placeholder
@app.command()
def explain(
    ffmpeg_command: str | None = typer.Argument(None, help="Existing ffmpeg command to explain"),
) -> None:
    """Explain an existing ffmpeg command in natural language.

    Placeholder for future feature to reverse-engineer ffmpeg commands
    into human-readable explanations.

    Args:
        ffmpeg_command: The ffmpeg command to explain

    Raises:
        typer.Exit: When no command is provided or feature is not implemented
    """
    if not ffmpeg_command:
        console.print("[red]❌ Error:[/red] Provide an ffmpeg command to explain.")
        raise typer.Exit(2)
    console.print("[yellow]⚠️ Warning:[/yellow] Explanation is not implemented in MVP.")


@app.command()
def enhance(
    prompt: str = typer.Argument(..., help="User prompt to enhance and analyze"),
    show_suggestions: bool = typer.Option(
        True, "--suggestions/--no-suggestions", help="Show improvement suggestions"
    ),
) -> None:
    """Enhance and analyze a user prompt for better LLM understanding.

    Uses the prompt enhancer to improve user input and provides suggestions
    for better prompt writing.

    Args:
        prompt: User prompt to enhance and analyze
        show_suggestions: Whether to display improvement suggestions

    Raises:
        typer.Exit: On error conditions
    """
    try:
        from .context_scanner_basic import scan
        from .prompt_enhancer import enhance_user_prompt
        from .prompt_enhancer import get_prompt_suggestions

        # Enhance the prompt using context-aware processing
        context = scan()

        enhanced = enhance_user_prompt(prompt, context)

        # Display original and enhanced prompts in a panel
        prompt_panel = Panel(
            f"[bold]Original:[/bold] {prompt}\n\n[bold]Enhanced:[/bold] {enhanced}",
            title="[bold green]Prompt Enhancement[/bold green]",
            border_style="green",
        )
        console.print(prompt_panel)

        # Show improvement suggestions if requested
        if show_suggestions:
            suggestions = get_prompt_suggestions(prompt)
            if suggestions:
                suggestion_table = Table(title="[bold yellow]Improvement Suggestions[/bold yellow]")
                suggestion_table.add_column("#", style="bold cyan", justify="center")
                suggestion_table.add_column("Suggestion", style="white")

                for i, suggestion in enumerate(suggestions, 1):
                    suggestion_table.add_row(str(i), suggestion)

                console.print(suggestion_table)
            else:
                console.print("\n[green]Prompt looks good![/green]")

        # Display available file context information in a table
        context_table = Table(title="[bold blue]Available Files[/bold blue]")
        context_table.add_column("Type", style="bold cyan", justify="center")
        context_table.add_column("Count", style="bold green", justify="center")
        context_table.add_column("Details", style="white")

        videos = context.get("videos")
        if videos and isinstance(videos, list):
            most_recent = context.get("most_recent_video")
            most_recent_name = Path(str(most_recent)).name if most_recent else "None"
            context_table.add_row(
                "Videos",
                str(len(videos)),
                f"Most recent: {most_recent_name}",
            )

        audios = context.get("audios")
        if audios and isinstance(audios, list):
            audio_names = [Path(str(a)).name for a in audios[:3]]
            context_table.add_row(
                "Audio",
                str(len(audios)),
                f"Files: {', '.join(audio_names)}",
            )

        subtitle_files = context.get("subtitle_files")
        if subtitle_files and isinstance(subtitle_files, list):
            subtitle_names = [Path(str(s)).name for s in subtitle_files[:3]]
            context_table.add_row(
                "Subtitles",
                str(len(subtitle_files)),
                f"Files: {', '.join(subtitle_names)}",
            )

        if context_table.row_count > 0:
            console.print(context_table)

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
