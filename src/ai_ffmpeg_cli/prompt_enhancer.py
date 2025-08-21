"""Prompt enhancement utilities for ai-ffmpeg-cli.

This module provides utilities to enhance and normalize user prompts
before sending them to the LLM, improving the accuracy and consistency
of generated ffmpeg commands.
"""

from __future__ import annotations

import re
from typing import Any


class PromptEnhancer:
    """Enhances user prompts to improve LLM command generation accuracy.

    This class applies pattern matching and context-aware enhancements
    to normalize user input and add missing technical details that help
    the LLM generate more accurate ffmpeg commands.
    """

    def __init__(self) -> None:
        """Initialize the prompt enhancer with predefined pattern mappings.

        Sets up regex patterns for common user expressions and their
        enhanced equivalents, along with file extension mappings for
        context-aware processing.
        """
        # Common patterns and their enhanced versions
        self.patterns = [
            # Aspect ratio patterns
            (
                r"\b(?:make|convert|resize|scale)\s+(?:to\s+)?(\d+):(\d+)\s+(?:aspect\s+)?ratio\b",
                r"convert to \1:\2 aspect ratio",
            ),
            (r"\b(\d+):(\d+)\s+(?:aspect\s+)?ratio\b", r"\1:\2 aspect ratio"),
            # Resolution patterns
            (r"\b(\d{3,4})[xX](\d{3,4})\b", r"\1x\2 resolution"),
            (r"\b(\d{3,4})p\b", r"\1p resolution"),
            # Social media platform patterns
            (
                r"\b(?:for\s+)?(?:Instagram|IG)\s+(?:Reels?|Stories?|Posts?)\b",
                r"for Instagram Reels (9:16 aspect ratio, 1080x1920)",
            ),
            (
                r"\b(?:for\s+)?(?:TikTok|Tik\s+Tok)\b",
                r"for TikTok (9:16 aspect ratio, 1080x1920)",
            ),
            (
                r"\b(?:for\s+)?(?:YouTube|YT)\s+(?:Shorts?)\b",
                r"for YouTube Shorts (9:16 aspect ratio, 1080x1920)",
            ),
            (
                r"\b(?:for\s+)?(?:YouTube|YT)\s+(?:videos?)\b",
                r"for YouTube videos (16:9 aspect ratio, 1920x1080)",
            ),
            (
                r"\b(?:for\s+)?(?:Twitter|X)\s+(?:videos?)\b",
                r"for Twitter videos (16:9 aspect ratio, 1920x1080)",
            ),
            (
                r"\b(?:for\s+)?(?:Facebook|FB)\s+(?:videos?)\b",
                r"for Facebook videos (16:9 aspect ratio, 1920x1080)",
            ),
            # Quality patterns
            (r"\b(?:high|good|better)\s+quality\b", r"high quality (lower CRF value)"),
            (
                r"\b(?:low|small|compressed)\s+(?:file\s+)?size\b",
                r"small file size (higher CRF value)",
            ),
            (r"\b(?:compress|reduce\s+size)\b", r"compress for smaller file size"),
            # Audio patterns
            (r"\b(?:remove|delete|strip)\s+audio\b", r"remove audio track"),
            (r"\b(?:extract|get)\s+audio\b", r"extract audio to separate file"),
            (r"\b(?:mute|silence)\b", r"remove audio track"),
            # Video patterns
            (
                r"\b(?:trim|cut)\s+(?:from|at)\s+(\d+(?:\.\d+)?)\s+(?:to|until)\s+(\d+(?:\.\d+)?)\b",
                r"trim from \1 seconds to \2 seconds",
            ),
            (
                r"\b(?:trim|cut)\s+(?:from|at)\s+(\d+:\d+:\d+(?:\.\d+)?)\s+(?:to|until)\s+(\d+:\d+:\d+(?:\.\d+)?)\b",
                r"trim from \1 to \2",
            ),
            (r"\b(?:speed\s+up|fast|faster)\b", r"increase playback speed"),
            (r"\b(?:slow\s+down|slow|slower)\b", r"decrease playback speed"),
            # Subtitle patterns
            (
                r"\b(?:add|burn|embed)\s+(?:captions?|subtitles?)\b",
                r"burn in subtitles",
            ),
            (
                r"\b(?:hardcode|hard\s+code)\s+(?:captions?|subtitles?)\b",
                r"burn in subtitles",
            ),
            (r"\b(?:soft\s+)?subtitles?\b", r"subtitles"),
            # Format patterns
            (
                r"\b(?:convert\s+to|save\s+as)\s+(mp4|avi|mov|mkv|webm)\b",
                r"convert to \1 format",
            ),
            # Common shortcuts
            (
                r"\b(?:make\s+it\s+)?vertical\b",
                r"convert to 9:16 aspect ratio (vertical)",
            ),
            (
                r"\b(?:make\s+it\s+)?horizontal\b",
                r"convert to 16:9 aspect ratio (horizontal)",
            ),
            (r"\b(?:make\s+it\s+)?square\b", r"convert to 1:1 aspect ratio (square)"),
            (r"\b(?:crop|fill)\s+(?:to\s+)?(\d+:\d+)\b", r"crop to \1 aspect ratio"),
            (r"\b(?:pad|letterbox)\s+(?:to\s+)?(\d+:\d+)\b", r"pad to \1 aspect ratio"),
            # Duration patterns
            (
                r"\b(\d+)\s+(?:second|sec)s?\s+(?:animated\s+)?gif\b",
                r"\1 second duration animated gif",
            ),
            (
                r"\b(\d+)\s+(?:second|sec)s?\s+(?:long\s+)?(?:video|clip)\b",
                r"\1 second duration video",
            ),
            (
                r"\b(\d+)\s+(?:second|sec)s?\s+(?:duration|length)\b",
                r"\1 second duration",
            ),
            (
                r"\b(?:for|with)\s+(\d+)\s+(?:second|sec)s?\b",
                r"with \1 second duration",
            ),
            (r"\b(\d+)s\s+(?:animated\s+)?gif\b", r"\1 second duration animated gif"),
            (r"\b(\d+)s\s+(?:long\s+)?(?:video|clip)\b", r"\1 second duration video"),
        ]

        # File extension patterns for better context
        self.file_extensions = {
            "video": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
            "audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "subtitle": [".srt", ".ass", ".ssa", ".vtt", ".sub"],
        }

    def enhance_prompt(self, prompt: str, context: dict[str, Any]) -> str:
        """Enhance a user prompt to improve LLM understanding.

        Applies a series of transformations to normalize user input and add
        context-aware details that help the LLM generate more accurate
        ffmpeg commands.

        Args:
            prompt: Original user prompt string
            context: Dictionary containing file context information (videos,
                    audios, subtitle_files, etc.)

        Returns:
            Enhanced prompt string with improved clarity and specificity

        Side effects:
            None - this is a pure function
        """
        enhanced = prompt.strip()

        # Apply pattern replacements in order of specificity
        for pattern, replacement in self.patterns:
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)

        # Add context-aware enhancements based on available files
        enhanced = self._add_context_enhancements(enhanced, context)

        # Add missing technical details that would help the LLM
        enhanced = self._add_missing_details(enhanced)

        # Normalize common terms for consistency
        enhanced = self._normalize_terms(enhanced)

        return enhanced.strip()

    def _add_context_enhancements(self, prompt: str, context: dict[str, Any]) -> str:
        """Add context-aware enhancements based on available files.

        Analyzes the context dictionary to identify available files and
        adds relevant information to the prompt when appropriate.

        Args:
            prompt: Current enhanced prompt
            context: File context dictionary

        Returns:
            Prompt with context-specific enhancements added
        """
        enhancements = []

        # Check for video files and add context if relevant
        if context.get("videos"):
            video_files = context["videos"]
            if len(video_files) == 1:
                enhancements.append(f"using video file: {video_files[0]}")
            elif len(video_files) > 1:
                enhancements.append(f"using one of {len(video_files)} available video files")

        # Check for subtitle files when subtitle operations are mentioned
        if context.get("subtitle_files"):
            subtitle_files = context["subtitle_files"]
            if "subtitle" in prompt.lower() or "caption" in prompt.lower():
                if len(subtitle_files) == 1:
                    enhancements.append(f"using subtitle file: {subtitle_files[0]}")
                elif len(subtitle_files) > 1:
                    enhancements.append(
                        f"using one of {len(subtitle_files)} available subtitle files"
                    )

        # Check for audio files when audio operations are mentioned
        if context.get("audios"):
            audio_files = context["audios"]
            if "audio" in prompt.lower() and len(audio_files) > 0:
                enhancements.append(f"using one of {len(audio_files)} available audio files")

        # Append all enhancements to the prompt
        if enhancements:
            prompt += f" ({', '.join(enhancements)})"

        return prompt

    def _add_missing_details(self, prompt: str) -> str:
        """Add missing technical details that would help the LLM.

        Identifies common scenarios where additional technical specifications
        would improve command generation accuracy.

        Args:
            prompt: Current enhanced prompt

        Returns:
            Prompt with missing details added as suggestions
        """
        details = []

        # Suggest resolution when aspect ratio is mentioned but no resolution specified
        if re.search(r"\b\d+:\d+\s+aspect\s+ratio\b", prompt, re.IGNORECASE):
            if "9:16" in prompt and "resolution" not in prompt.lower():
                details.append("suggest 1080x1920 resolution")
            elif "16:9" in prompt and "resolution" not in prompt.lower():
                details.append("suggest 1920x1080 resolution")
            elif "1:1" in prompt and "resolution" not in prompt.lower():
                details.append("suggest 1080x1080 resolution")

        # Suggest CRF values when quality is mentioned but no specific settings
        if "quality" in prompt.lower() and "crf" not in prompt.lower():
            if "high" in prompt.lower():
                details.append("use CRF 18-23 for high quality")
            elif "low" in prompt.lower() or "small" in prompt.lower():
                details.append("use CRF 28-32 for smaller file size")

        # Suggest codec when format conversion is mentioned but no codec specified
        if (
            any(ext in prompt.lower() for ext in [".mp4", ".avi", ".mov", ".mkv"])
            and "codec" not in prompt.lower()
        ):
            details.append("use appropriate codec for target format")

        # Append all details to the prompt
        if details:
            prompt += f" ({', '.join(details)})"

        return prompt

    def _normalize_terms(self, prompt: str) -> str:
        """Normalize common terms for consistency.

        Standardizes formatting and expands common abbreviations to
        improve LLM understanding.

        Args:
            prompt: Current enhanced prompt

        Returns:
            Prompt with normalized terms
        """
        # Normalize aspect ratio formatting (remove spaces around colons)
        prompt = re.sub(r"\b(\d+)\s*:\s*(\d+)\b", r"\1:\2", prompt)

        # Normalize resolution formatting (remove spaces around 'x')
        prompt = re.sub(r"\b(\d{3,4})\s*[xX]\s*(\d{3,4})\b", r"\1x\2", prompt)

        # Expand common abbreviations to full terms
        replacements = {
            "vid": "video",
            "aud": "audio",
            "sub": "subtitle",
            "cap": "caption",
            "res": "resolution",
            "fps": "frame rate",
            "bitrate": "bit rate",
            "codec": "encoding format",
        }

        for abbrev, full in replacements.items():
            prompt = re.sub(rf"\b{abbrev}\b", full, prompt, flags=re.IGNORECASE)

        return prompt

    def suggest_improvements(self, prompt: str) -> list[str]:
        """Suggest improvements for a given prompt.

        Analyzes the prompt for common issues that could lead to
        inaccurate or incomplete ffmpeg command generation.

        Args:
            prompt: User prompt to analyze

        Returns:
            List of improvement suggestions as strings
        """
        suggestions = []

        # Check for vague terms that lack specificity
        vague_terms = ["better", "good", "nice", "proper", "correct", "right"]
        for term in vague_terms:
            if term in prompt.lower():
                suggestions.append(
                    f"Replace '{term}' with specific requirements (e.g., 'high quality', 'small file size')"
                )

        # Check for missing file format specifications
        if "file" in prompt.lower() and not re.search(r"\.[a-zA-Z0-9]+", prompt):
            suggestions.append("Specify file format (e.g., .mp4, .avi)")

        # Check for missing quality specifications when quality is mentioned
        if "quality" in prompt.lower() and "crf" not in prompt.lower():
            suggestions.append("Specify quality level (e.g., 'high quality', 'small file size')")

        # Check for missing aspect ratio when resizing operations are mentioned
        if any(word in prompt.lower() for word in ["resize", "scale", "convert"]) and not re.search(
            r"\d+:\d+", prompt
        ):
            suggestions.append("Specify target aspect ratio (e.g., '16:9', '9:16', '1:1')")

        return suggestions


def enhance_user_prompt(prompt: str, context: dict[str, Any]) -> str:
    """Convenience function to enhance a user prompt.

    Creates a PromptEnhancer instance and applies enhancement to the
    given prompt. Use this for one-off prompt enhancement.

    Args:
        prompt: Original user prompt string
        context: File context information dictionary

    Returns:
        Enhanced prompt string
    """
    enhancer = PromptEnhancer()
    return enhancer.enhance_prompt(prompt, context)


def get_prompt_suggestions(prompt: str) -> list[str]:
    """Get suggestions for improving a user prompt.

    Creates a PromptEnhancer instance and analyzes the prompt for
    potential improvements. Use this for providing user feedback.

    Args:
        prompt: User prompt string to analyze

    Returns:
        List of improvement suggestions as strings
    """
    enhancer = PromptEnhancer()
    return enhancer.suggest_improvements(prompt)
