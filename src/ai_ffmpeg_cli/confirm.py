"""User confirmation utilities for ai-ffmpeg-cli.

This module provides utilities for prompting users for confirmation
before executing potentially destructive operations.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

# Initialize console for Rich output
console = Console()


def confirm_prompt(question: str, default_yes: bool = True, assume_yes: bool = False) -> bool:
    """Prompt user for confirmation with configurable defaults.

    Displays a confirmation prompt to the user and returns their response.
    Supports configurable defaults and automatic yes responses for
    non-interactive scenarios.

    Args:
        question: The question to ask the user
        default_yes: Whether the default response should be yes (Y/n vs y/N)
        assume_yes: Whether to automatically return True without prompting

    Returns:
        True if user confirms, False if user declines

    Note:
        Handles EOFError gracefully by returning the default response
    """
    if assume_yes:
        return True

    # Set up the prompt with appropriate default indicator
    default_choice = "Y" if default_yes else "N"

    # Create styled confirmation prompt
    prompt_text = Text()
    prompt_text.append(question, style="bold white")

    # Create confirmation panel
    confirm_panel = Panel(
        prompt_text,
        title="[bold cyan]Confirmation Required[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    try:
        console.print(confirm_panel)
        # Use Rich's Confirm prompt for better integration
        is_affirmative = Confirm.ask(
            "",
            default=default_yes,
            show_default=False,  # We already show the default in the panel
            console=console,
        )

        # Show user's choice
        choice_display = "Yes" if is_affirmative else "No"
        console.print(f"[dim]User choice: {choice_display}[/dim]")

        return is_affirmative

    except EOFError:
        # Handle Ctrl+D gracefully by returning default
        console.print(f"[dim]Using default: {default_choice}[/dim]")
        return default_yes
