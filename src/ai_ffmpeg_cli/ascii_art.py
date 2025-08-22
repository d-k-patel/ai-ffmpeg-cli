"""ASCII art module for ai-ffmpeg-cli.

This module provides colorful ASCII art displays using pyfiglet
with colors relevant to video and audio processing.
"""

from __future__ import annotations

import random
import shutil

import pyfiglet
from rich.console import Console
from rich.text import Text

# Initialize console for Rich output
console = Console()


def get_terminal_width() -> int:
    """Get the current terminal width.

    Returns:
        Terminal width in characters, defaults to 80 if cannot be determined
    """
    try:
        return shutil.get_terminal_size().columns
    except (OSError, AttributeError):
        return 80


def center_text(text: str, width: int) -> str:
    """Center-align text within a given width.

    Args:
        text: Text to center
        width: Total width to center within

    Returns:
        Center-aligned text
    """
    lines = text.split("\n")
    centered_lines = []

    for line in lines:
        if line.strip():
            # Calculate padding to center the line
            padding = max(0, (width - len(line)) // 2)
            centered_line = " " * padding + line
        else:
            centered_line = line
        centered_lines.append(centered_line)

    return "\n".join(centered_lines)


def get_ascii_art(text: str = "AICLIP", font: str = "slant") -> str:
    """Generate ASCII art using pyfiglet.

    Args:
        text: Text to convert to ASCII art
        font: Pyfiglet font to use

    Returns:
        ASCII art string
    """
    try:
        fig = pyfiglet.Figlet(font=font)
        ascii_art = fig.renderText(text)

        # Center the ASCII art based on terminal width
        terminal_width = get_terminal_width()
        centered_art = center_text(ascii_art, terminal_width)

        return centered_art
    except Exception:
        # Fallback to a simple ASCII art if pyfiglet fails
        fallback_art = f"""
╔══════════════════════════════════════════════════════════════╗
║                        {text}                                ║
╚══════════════════════════════════════════════════════════════╝
"""
        terminal_width = get_terminal_width()
        return center_text(fallback_art, terminal_width)


def display_colored_ascii_art(
    text: str = "AICLIP",
    font: str = "slant",
    primary_color: str = "cyan",
    secondary_color: str = "blue",
    accent_color: str = "green",
) -> None:
    """Display colorful ASCII art with video/audio processing theme colors.

    Args:
        text: Text to display as ASCII art
        font: Pyfiglet font to use
        primary_color: Main color for the text (cyan - represents video/technology)
        secondary_color: Secondary color for accents (blue - represents audio/water)
        accent_color: Accent color for highlights (green - represents success/processing)
    """
    ascii_art = get_ascii_art(text, font)

    # Create colored text with gradient effect
    colored_text = Text()

    # Split the ASCII art into lines
    lines = ascii_art.split("\n")

    for i, line in enumerate(lines):
        if not line.strip():
            colored_text.append("\n")
            continue

        # Create a gradient effect using different colors
        for j, char in enumerate(line):
            if char.isspace():
                colored_text.append(char)
            else:
                # Alternate between primary and secondary colors for gradient effect
                if (i + j) % 3 == 0:
                    colored_text.append(char, style=f"bold {primary_color}")
                elif (i + j) % 3 == 1:
                    colored_text.append(char, style=f"bold {secondary_color}")
                else:
                    colored_text.append(char, style=f"bold {accent_color}")

        colored_text.append("\n")

    # Display the colored ASCII art
    console.print(colored_text)

    # Add a subtitle with accent color, center-aligned
    subtitle = Text()
    subtitle.append("AI-Powered Video & Audio Processing", style=f"italic {accent_color}")
    console.print(subtitle, justify="center")
    console.print()


def display_welcome_banner() -> None:
    """Display a welcome banner with ASCII art and project information."""
    # Display the main ASCII art
    display_colored_ascii_art()

    # Add a decorative line, center-aligned
    terminal_width = get_terminal_width()
    line_length = min(60, terminal_width - 4)  # Leave some margin
    padding = max(0, (terminal_width - line_length) // 2)
    decorative_line = " " * padding + "─" * line_length
    console.print(decorative_line, style="dim cyan")
    console.print()


def get_random_font() -> str:
    """Get a random pyfiglet font for variety.

    Returns:
        Random font name
    """
    fonts = [
        "slant",
        "banner",
        "big",
        "block",
        "bubble",
        "digital",
        "isometric1",
        "isometric2",
        "isometric3",
        "isometric4",
        "letters",
        "alligator",
        "dotmatrix",
        "bubblehead",
        "bulbhead",
        "chunky",
        "coinstak",
        "colossal",
        "crawford",
        "diamond",
        "epic",
        "fender",
        "fourtops",
        "goofy",
        "graceful",
        "hollywood",
        "invita",
        "isometric1",
        "isometric2",
        "isometric3",
        "isometric4",
        "italic",
        "larry3d",
        "lcd",
        "lean",
        "letters",
        "alligator2",
        "alligator3",
        "alphabet",
        "arrows",
        "avatar",
        "banner3-D",
        "banner3",
        "banner4",
        "barbwire",
        "basic",
        "bell",
        "bigchief",
        "binary",
        "block",
        "bubble",
        "caligraphy",
        "caligraphy2",
        "catwalk",
        "chunky",
        "coinstak",
        "colossal",
        "computer",
        "contessa",
        "contrast",
        "cosmic",
        "cosmike",
        "crawford",
        "crawford2",
        "crazy",
        "cricket",
        "cyberlarge",
        "cybermedium",
        "cybersmall",
        "diamond",
        "digital",
        "doh",
        "doom",
        "dotmatrix",
        "drpepper",
        "eftichess",
        "eftifont",
        "eftipiti",
        "eftirobot",
        "eftitalic",
        "eftiwall",
        "eftiwater",
        "epic",
        "fender",
        "fourtops",
        "fuzzy",
        "goofy",
        "gothic",
        "graceful",
        "gradient",
        "graffiti",
        "hollywood",
        "invita",
        "isometric1",
        "isometric2",
        "isometric3",
        "isometric4",
        "italic",
        "ivrit",
        "jacky",
        "katakana",
        "kban",
        "larry3d",
        "lcd",
        "lean",
        "letters",
        "linux",
        "lockergnome",
        "madrid",
        "marquee",
        "maxfour",
        "mike",
        "mini",
        "mirror",
        "mnemonic",
        "morse",
        "moscow",
        "nancyj",
        "nancyj-fancy",
        "nancyj-underlined",
        "nipples",
        "ntgreek",
        "o8",
        "ogre",
        "pawp",
        "peaks",
        "pebbles",
        "pepper",
        "poison",
        "puffy",
        "pyramid",
        "rectangles",
        "relief",
        "relief2",
        "rev",
        "roman",
        "rot13",
        "rounded",
        "rowancap",
        "rozzo",
        "runic",
        "runyc",
        "sblood",
        "script",
        "serifcap",
        "shadow",
        "short",
        "slant",
        "slide",
        "slscript",
        "small",
        "smisome1",
        "smkeyboard",
        "smscript",
        "smshadow",
        "smslant",
        "smtengwar",
        "speed",
        "stampatello",
        "standard",
        "starwars",
        "stellar",
        "stop",
        "straight",
        "tanja",
        "tengwar",
        "term",
        "thick",
        "thin",
        "threepoint",
        "ticks",
        "ticksslant",
        "tiles",
        "tinker-toy",
        "tombstone",
        "trek",
        "tsalagi",
        "twopoint",
        "univers",
        "usaflag",
        "wavy",
        "weird",
    ]

    return random.choice(fonts)


def display_dynamic_banner() -> None:
    """Display a dynamic banner with random font and colors."""
    # Choose a random font for variety
    font = get_random_font()

    # Display with the chosen font
    display_colored_ascii_art(font=font)
