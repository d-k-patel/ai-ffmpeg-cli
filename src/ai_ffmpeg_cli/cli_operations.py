"""CLI operations extracted from main.py for better testability."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich import print as rprint

from .command_builder import build_commands
from .confirm import confirm_prompt
from .context_scanner import scan
from .errors import BuildError
from .errors import ExecError
from .errors import ParseError
from .intent_router import route_intent
from .llm_client import LLMClient
from .llm_client import OpenAIProvider

if TYPE_CHECKING:
    from .config import AppConfig


def process_natural_language_prompt(
    prompt: str,
    config: AppConfig,
    assume_yes: bool = False,
) -> int:
    """Process a natural language prompt and execute the resulting ffmpeg commands.

    Args:
        prompt: Natural language prompt from user
        config: Application configuration
        assume_yes: Whether to skip confirmation prompts

    Returns:
        int: Exit code (0 for success, non-zero for failure)

    Raises:
        ParseError: If LLM parsing fails
        BuildError: If command building fails
        ExecError: If command execution fails
    """
    # Scan for context
    context = scan()

    # Create LLM client
    client = _make_llm_client(config)

    # Parse natural language to intent
    intent = client.parse(prompt, context, timeout=config.timeout_seconds)

    # Route intent to command plan
    plan = route_intent(intent)

    # Build ffmpeg commands
    commands = build_commands(plan, assume_yes=assume_yes)

    # Preview and execute
    return _execute_commands(commands, config, assume_yes)


def process_interactive_session(config: AppConfig, assume_yes: bool = False) -> int:
    """Run an interactive session for natural language ffmpeg operations.

    Args:
        config: Application configuration
        assume_yes: Whether to skip confirmation prompts

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    rprint("Enter natural language descriptions of ffmpeg operations.")
    rprint("Type 'exit', 'quit', or 'q' to exit.")
    rprint()

    while True:
        try:
            user_input = input("aiclip> ").strip()
            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ("exit", "quit", "q"):
                break

            # Process the command
            exit_code = process_natural_language_prompt(user_input, config, assume_yes)

            if exit_code != 0:
                rprint(f"[yellow]Command completed with exit code: {exit_code}[/yellow]")
            rprint()

        except (ParseError, BuildError, ExecError) as e:
            rprint(f"[red]Error:[/red] {e}")
            rprint()
        except KeyboardInterrupt:
            rprint("\nExiting...")
            break
        except EOFError:
            rprint("\nExiting...")
            break

    return 0


def _make_llm_client(config: AppConfig) -> LLMClient:
    """Create LLM client with secure API key handling.

    Args:
        config: Application configuration

    Returns:
        LLMClient: Configured LLM client

    Raises:
        ConfigError: If API key is invalid or missing
    """
    # This will validate the API key format and presence
    api_key = config.get_api_key_for_client()
    provider = OpenAIProvider(api_key=api_key, model=config.model)
    return LLMClient(provider)


def _execute_commands(
    commands: list[list[str]],
    config: AppConfig,
    assume_yes: bool = False,
) -> int:
    """Execute ffmpeg commands with preview and confirmation.

    Args:
        commands: List of ffmpeg command lists
        config: Application configuration
        assume_yes: Whether to skip confirmation prompts

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    from .executor import preview
    from .executor import run

    # Show preview and get confirmation
    preview(commands)
    confirmed = (
        True
        if assume_yes
        else confirm_prompt("Run these commands?", config.confirm_default, assume_yes)
    )

    return run(
        commands,
        confirm=confirmed,
        dry_run=config.dry_run,
        show_preview=False,  # Already shown above
        assume_yes=assume_yes,
    )


def setup_logging(verbose: bool) -> None:
    """Setup logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
