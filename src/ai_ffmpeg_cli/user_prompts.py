"""User confirmation utilities for ai-ffmpeg-cli.

This module provides user interaction utilities for confirming actions
before execution. It handles various confirmation scenarios with
configurable defaults and assumptions.
"""

from __future__ import annotations


def confirm_prompt(question: str, default_yes: bool = True, assume_yes: bool = False) -> bool:
    """Prompt user for confirmation with configurable defaults.

    Displays a confirmation prompt to the user and returns their response.
    Supports configurable defaults and automatic yes responses for
    non-interactive scenarios.

    Args:
        question: The question to ask the user
        default_yes: Whether the default response should be yes (affects prompt display)
        assume_yes: Whether to automatically return True without prompting

    Returns:
        bool: True if user confirms, False if user declines

    Examples:
        >>> confirm_prompt("Continue?", default_yes=True)
        Continue? [Y/n]
        >>> confirm_prompt("Delete file?", default_yes=False)
        Delete file? [y/N]
    """
    if assume_yes:
        return True

    # Format default indicator based on default_yes setting
    default = "Y/n" if default_yes else "y/N"

    try:
        resp = input(f"{question} [{default}] ").strip().lower()
    except EOFError:
        # Handle EOF (Ctrl+D) by returning default
        return default_yes

    # Empty response returns the default
    if not resp:
        return default_yes

    # Check for affirmative responses
    return resp in {"y", "yes"}
