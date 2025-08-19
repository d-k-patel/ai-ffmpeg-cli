"""CLI operations for ai-ffmpeg-cli.

This module contains the core CLI operations extracted from main.py for better
testability and separation of concerns. It handles both one-shot and interactive
modes of operation with comprehensive error handling and user feedback.

Key features:
- Natural language prompt processing
- Interactive session management
- LLM client initialization and management
- Command execution with preview and confirmation
- Comprehensive error handling and user feedback
- Logging setup and configuration

Processing pipeline:
1. Context scanning (available media files)
2. LLM parsing (natural language to intent)
3. Intent routing (intent to command plan)
4. Command building (plan to executable commands)
5. Preview and execution
"""

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

    Main processing function that takes a natural language prompt and converts
    it into executable ffmpeg commands through the complete processing pipeline.

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
    # Scan for context (available media files)
    context = scan()

    # Create LLM client with secure API key handling
    client = _make_llm_client(config)

    # Parse natural language to intent using LLM
    intent = client.parse(prompt, context, timeout=config.timeout_seconds)

    # Route intent to command plan with security validation
    plan = route_intent(intent)

    # Build ffmpeg commands from plan
    commands = build_commands(plan, assume_yes=assume_yes)

    # Preview and execute commands
    return _execute_commands(commands, config, assume_yes)


def process_interactive_session(config: AppConfig, assume_yes: bool = False) -> int:
    """Run an interactive session for natural language ffmpeg operations.

    Provides a REPL-style interface for processing multiple natural language
    commands in sequence. Handles user input, error recovery, and graceful exit.

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

            # Process the command through the full pipeline
            exit_code = process_natural_language_prompt(user_input, config, assume_yes)

            if exit_code != 0:
                rprint(f"[yellow]Command completed with exit code: {exit_code}[/yellow]")
            rprint()

        except (ParseError, BuildError, ExecError) as e:
            # Handle application-specific errors with user-friendly messages
            rprint(f"[red]Error:[/red] {e}")
            rprint()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            rprint("\nExiting...")
            break
        except EOFError:
            # Handle Ctrl+D gracefully
            rprint("\nExiting...")
            break

    return 0


def _make_llm_client(config: AppConfig) -> LLMClient:
    """Create LLM client with secure API key handling.

    Initializes the LLM client with proper API key validation and
    secure error handling. Ensures the client is ready for use.

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

    Handles the final stage of the processing pipeline: displaying
    command preview, getting user confirmation, and executing commands.

    Args:
        commands: List of ffmpeg command lists to execute
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

    # Execute commands with appropriate settings
    return run(
        commands,
        confirm=confirmed,
        dry_run=config.dry_run,
        show_preview=False,  # Already shown above
        assume_yes=assume_yes,
    )


def setup_logging(verbose: bool) -> None:
    """Setup logging configuration.

    Configures the logging system with appropriate level and format
    based on the verbose flag.

    Args:
        verbose: Whether to enable verbose logging (DEBUG level)
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
