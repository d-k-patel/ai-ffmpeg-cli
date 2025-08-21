"""LLM client implementation for ai-ffmpeg-cli.

This module provides the interface for communicating with Large Language Models
to parse natural language prompts into structured ffmpeg intents.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from .credential_security import create_secure_logger
from .credential_security import sanitize_error_message
from .custom_exceptions import ParseError
from .intent_models import FfmpegIntent

# Create secure logger that masks sensitive information
logger = create_secure_logger(__name__)


# Comprehensive system prompt that instructs the LLM on how to parse natural language
# into structured ffmpeg intents with specific schema requirements
SYSTEM_PROMPT = (
    "You are an expert assistant that translates natural language into ffmpeg intents.\n"
    "Respond ONLY with JSON matching the FfmpegIntent schema.\n"
    "\n"
    "Schema fields (all optional unless noted):\n"
    "  action (required): one of ['convert','trim','segment','overlay','thumbnail','extract_audio','compress','format_convert','extract_frames']\n"
    "  inputs: array of absolute file paths from context.videos / context.audios / context.images\n"
    "  output: null or string filename (must NOT equal any input path)\n"
    "  video_codec: e.g. 'libx264','libx265','copy'\n"
    "  audio_codec: e.g. 'aac','libopus','copy','none'\n"
    "  filters: ffmpeg filter chain string, filters separated by commas\n"
    "  start: start time (e.g. '00:00:05.000' or seconds number)\n"
    "  end: end time (same format as start). If both start and duration present, ignore end.\n"
    "  duration: seconds number or time string\n"
    "  scale: WxH string (e.g. '1920:1080'). Used ONLY if caller intends a simple scale; otherwise prefer 'filters'.\n"
    "  bitrate: target video bitrate like '4000k' (ignored if crf is set)\n"
    "  crf: integer CRF value (0=lossless, 18-28 common). Prefer CRF when present.\n"
    "  overlay_path: absolute image/video path (from context) for overlays if action requires\n"
    "  overlay_xy: overlay position like 'x=10:y=20'\n"
    "  fps: integer frames per second (e.g. 30)\n"
    "  glob: boolean; when true, inputs may include a single shell-style glob from context.images\n"
    "  extra_flags: array of additional ffmpeg CLI flags (strings)\n"
    "\n"
    "Context usage:\n"
    "  • Use ONLY paths present in context.videos, context.audios, or context.images.\n"
    "  • Never invent filenames. Never use placeholders like 'input.mp4'.\n"
    "  • If the user mentions a file that is not in context, return an error JSON (see Errors).\n"
    "\n"
    "Defaults and best practices:\n"
    "  • For 'convert' without explicit codecs: video_codec='libx264', audio_codec='aac'.\n"
    "  • For 'compress': video_codec='libx265', crf=28, audio_codec='aac'.\n"
    "  • For format conversion (e.g., to GIF, WebM, AVI): use 'convert' action with appropriate filters and codecs.\n"
    "    - GIF: use 'convert' with filters='fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse'\n"
    "    - WebM: use 'convert' with video_codec='libvpx-vp9', audio_codec='libopus'\n"
    "    - AVI: use 'convert' with video_codec='libx264', audio_codec='mp3'\n"
    "  • Use 'format_convert' only when the user explicitly asks for a specific container format with default codecs.\n"
    "  • Always ensure even dimensions with H.264/H.265. Use scale expressions that guarantee even sizes,\n"
    "    e.g. scale=trunc(iw*0.5/2)*2:trunc(ih*0.5/2)*2 or force_original_aspect_ratio=decrease followed by pad with even ow/oh.\n"
    "  • Prefer CRF over bitrate unless user explicitly asks for a bitrate.\n"
    "  • Add 'yuv420p' pixel format and '+faststart' for web/social compatibility:\n"
    "    extra_flags should include ['-pix_fmt','yuv420p','-movflags','+faststart'] unless user forbids.\n"
    "  • If audio is not mentioned and exists, transcode to AAC at a reasonable default (e.g. 128k); if user says 'no audio', set audio_codec='none'.\n"
    "  • If fps is requested, include -r via fps field (integer).\n"
    "  • If duration is requested (e.g., '5 second GIF'), use duration field (number or time string).\n"
    "\n"
    "Aspect ratio & resizing rules:\n"
    "  • For target AR changes (e.g. Instagram Reels 9:16, 1080x1920):\n"
    "    - If user says 'crop' or 'fill', use: scale=-2:1920:force_original_aspect_ratio=increase, then crop=1080:1920 centered.\n"
    "    - If user says 'pad' or 'no crop', use: scale=1080:-2:force_original_aspect_ratio=decrease, then pad=1080:1920:(ow-iw)/2:(oh-ih)/2.\n"
    "    - Ensure final width/height are even.\n"
    "  • If user gives only AR (e.g. 'make 9:16') and no resolution, infer 1080x1920 for vertical or 1920x1080 for horizontal.\n"
    "\n"
    "Subtitles (burn-in):\n"
    "  • Use the 'subtitles=' filter when the user requests visible/burned captions.\n"
    "  • Styling (ASS force_style) goes inside the subtitles filter only. Example:\n"
    "    subtitles=/abs/path.srt:force_style='Fontsize=36,Outline=2,Shadow=1,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&'\n"
    "  • Combine filters with commas, e.g.: scale=1080:-2:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles=/abs/path.srt\n"
    "\n"
    "Filter chain rules:\n"
    "  • Filters must be comma-separated in a single chain string.\n"
    "  • Options like force_original_aspect_ratio apply ONLY to the scale filter, not to crop/subtitles.\n"
    "  • Do NOT place unrelated options after subtitles. Each filter has its own parameters.\n"
    "\n"
    "Output safety:\n"
    "  • Never set output to any input path. If omitted, the system will auto-name.\n"
    "  • If user requests a container that conflicts with codecs (e.g. .mp4 with vp9), keep the container as requested but select compatible defaults if unspecified.\n"
    "\n"
    "Multiple inputs:\n"
    "  • For concat of files with identical codecs, set action='concat' and provide inputs; filters may be empty. Otherwise use concat demuxing guidance implied by the user request.\n"
    "\n"
    "Trimming:\n"
    "  • Respect start/end/duration. If both end and duration are given, prefer duration.\n"
    "  • When user specifies a time limit (e.g., '5 second', '10s', '30 seconds'), use the duration field.\n"
    "  • Duration can be specified as a number (seconds) or time string (e.g., '00:00:05').\n"
    "  • IMPORTANT: When user asks for a specific duration (e.g., '5 second GIF', '10 second video'),\n"
    "    ALWAYS include the duration field in the response.\n"
    "\n"
    "Errors:\n"
    "  • If the user asks for an action you cannot express, reply ONLY with:\n"
    '      {"error":"unsupported_action","message":"<short reason>"}\n'
    "  • If required files are not in context, reply ONLY with:\n"
    '      {"error":"missing_input","message":"File not found in context: <name>"}\n'
    "\n"
    "Quoting & portability:\n"
    "  • Do not include shell quoting (no surrounding quotes). Provide plain values; the caller will add shell quotes.\n"
    "  • Use absolute paths exactly as given in context.\n"
    "\n"
    "Examples (illustrative only — always use real context paths):\n"
    "  • Instagram Reel (crop/fill): action='convert', filters='scale=-2:1920:force_original_aspect_ratio=increase,crop=1080:1920'\n"
    "  • Instagram Reel (pad): action='convert', filters='scale=1080:-2:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2'\n"
    "  • Convert to GIF: action='convert', filters='fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse', video_codec='gif', audio_codec='none'\n"
    "  • Convert to GIF with duration: action='convert', filters='fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse', video_codec='gif', audio_codec='none', duration=5\n"
    "  • 5 second GIF: action='convert', filters='fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse', video_codec='gif', audio_codec='none', duration=5\n"
    "  • 10 second video clip: action='convert', video_codec='libx264', audio_codec='aac', duration=10\n"
    "  • Convert to WebM: action='convert', video_codec='libvpx-vp9', audio_codec='libopus'\n"
    "  • Burn subtitles: add ',subtitles=/abs/path.srt' at the end of the chain.\n"
    "\n"
    "Final instruction:\n"
    "  • Return ONLY the JSON object for FfmpegIntent (or the JSON error). No prose, no code fences."
)


class LLMProvider:
    """Abstract base class for LLM providers.

    Defines the interface that all LLM providers must implement
    for natural language to intent parsing.
    """

    def complete(self, system: str, user: str, timeout: int) -> str:  # pragma: no cover - interface
        """Complete a chat request with the LLM.

        Args:
            system: System prompt defining the task
            user: User message to process
            timeout: Request timeout in seconds

        Returns:
            Raw response from the LLM

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation.

    Handles communication with OpenAI's chat completion API,
    including error handling and response processing.
    """

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize OpenAI provider with API key and model.

        Args:
            api_key: OpenAI API key for authentication
            model: Model name to use for completions

        Raises:
            Exception: When client initialization fails
        """
        from openai import OpenAI  # lazy import for testability

        # Never log the actual API key
        logger.debug(f"Initializing OpenAI provider with model: {model}")

        try:
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except Exception as e:
            # Sanitize error message to prevent API key exposure
            sanitized_error = sanitize_error_message(str(e))
            logger.error(f"Failed to initialize OpenAI client: {sanitized_error}")
            raise

    def complete(self, system: str, user: str, timeout: int) -> str:
        """Complete chat request with error handling and retries.

        Sends a chat completion request to OpenAI with comprehensive
        error handling for various failure scenarios.

        Args:
            system: System prompt defining the task
            user: User message to process
            timeout: Request timeout in seconds

        Returns:
            Raw response content from OpenAI

        Raises:
            ParseError: When the request fails with specific error details
        """
        try:
            logger.debug(f"Making OpenAI API request with model: {self.model}, timeout: {timeout}s")

            rsp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},  # Ensure JSON response
                timeout=timeout,
            )

            content = rsp.choices[0].message.content or "{}"
            logger.debug(f"Received response length: {len(content)} characters")
            return content

        except Exception as e:
            # Import specific exception types for better handling
            try:
                from openai import APIError
                from openai import APITimeoutError
                from openai import AuthenticationError
                from openai import RateLimitError

                if isinstance(e, AuthenticationError):
                    # Never log the actual API key in authentication errors
                    logger.error("OpenAI authentication failed - check API key format and validity")
                    raise ParseError(
                        "OpenAI authentication failed. Please verify your API key is correct and active. "
                        "Get a valid key from https://platform.openai.com/api-keys"
                    ) from e

                elif isinstance(e, RateLimitError):
                    logger.error("OpenAI rate limit exceeded")
                    raise ParseError(
                        "OpenAI rate limit exceeded. Please wait a moment and try again, "
                        "or check your usage limits at https://platform.openai.com/usage"
                    ) from e

                elif isinstance(e, APITimeoutError):
                    logger.error(f"OpenAI request timed out after {timeout}s")
                    raise ParseError(
                        f"OpenAI request timed out after {timeout} seconds. "
                        "Try increasing --timeout or check your internet connection."
                    ) from e

                elif isinstance(e, APIError):
                    sanitized_error = sanitize_error_message(str(e))
                    logger.error(f"OpenAI API error: {sanitized_error}")
                    raise ParseError(
                        f"OpenAI API error: {sanitized_error}. "
                        "This may be a temporary service issue. Please try again."
                    ) from e

            except ImportError:
                # Fallback for older openai versions
                pass

            # Generic error handling for unknown exceptions
            sanitized_error = sanitize_error_message(str(e))
            logger.error(f"Unexpected error during OpenAI request: {sanitized_error}")
            raise ParseError(
                f"Failed to get response from OpenAI: {sanitized_error}. "
                "Please check your internet connection and try again."
            ) from e


class LLMClient:
    """High-level LLM client for parsing natural language into ffmpeg intents.

    Provides a unified interface for natural language processing with
    retry logic, error handling, and response validation.
    """

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize LLM client with a provider.

        Args:
            provider: LLM provider instance to use for completions
        """
        self.provider = provider

    def parse(
        self, nl_prompt: str, context: dict[str, Any], timeout: int | None = None
    ) -> FfmpegIntent:
        """Parse natural language prompt into FfmpegIntent with retry logic.

        Processes a natural language prompt through the LLM to generate
        a structured ffmpeg intent. Includes input sanitization, prompt
        enhancement, and retry logic for failed parsing attempts.

        Args:
            nl_prompt: Natural language prompt from user
            context: File context information containing available files
            timeout: Request timeout in seconds (defaults to 60)

        Returns:
            FfmpegIntent: Parsed and validated intent object

        Raises:
            ParseError: If parsing fails after retry attempts or validation errors
        """
        # Sanitize user input first to prevent injection attacks
        from .file_operations import sanitize_user_input
        from .prompt_enhancer import enhance_user_prompt

        sanitized_prompt = sanitize_user_input(nl_prompt)

        if not sanitized_prompt.strip():
            raise ParseError(
                "Empty or invalid prompt provided. Please provide a clear description of what you want to do."
            )

        # Enhance the prompt for better LLM understanding using context
        enhanced_prompt = enhance_user_prompt(sanitized_prompt, context)

        # Log the enhancement for debugging
        if enhanced_prompt != sanitized_prompt:
            logger.debug(f"Enhanced prompt: '{sanitized_prompt}' -> '{enhanced_prompt}'")

        # Prepare user payload with prompt and context
        user_payload = json.dumps({"prompt": enhanced_prompt, "context": context})
        effective_timeout = 60 if timeout is None else timeout

        logger.debug(f"Parsing prompt with timeout: {effective_timeout}s")

        # First attempt at parsing
        try:
            raw = self.provider.complete(SYSTEM_PROMPT, user_payload, timeout=effective_timeout)
            logger.debug(f"Received raw response: {len(raw)} chars")

            data = json.loads(raw)

            # Check if the response is an error JSON from the AI
            if isinstance(data, dict) and "error" in data:
                error_type = data.get("error", "unknown_error")
                error_message = data.get("message", "Unknown error")

                if error_type == "missing_input":
                    raise ParseError(
                        f"Input file not found: {error_message}. "
                        "Please ensure the file exists in the current directory and try again."
                    )
                elif error_type == "unsupported_action":
                    raise ParseError(
                        f"Unsupported operation: {error_message}. "
                        "Please check the supported actions and try a different approach."
                    )
                else:
                    raise ParseError(
                        f"AI model error: {error_message}. "
                        "Please try rephrasing your request or check if the operation is supported."
                    )

            intent = FfmpegIntent.model_validate(data)
            logger.debug(f"Successfully parsed intent: {intent.action}")
            return intent

        except (json.JSONDecodeError, ValidationError) as first_err:
            # Log the specific parsing error for debugging
            logger.debug(f"Primary parse failed: {type(first_err).__name__}: {first_err}")

            # One corrective pass with more specific instructions
            logger.debug("Attempting repair with corrective prompt")
            repair_prompt = (
                "The previous JSON output was invalid. Please generate ONLY valid JSON "
                "matching the FfmpegIntent schema. Do not include any explanations or markdown formatting."
            )

            try:
                raw2 = self.provider.complete(
                    SYSTEM_PROMPT,
                    repair_prompt + "\n" + user_payload,
                    timeout=effective_timeout,
                )

                data2 = json.loads(raw2)

                # Check if the retry response is an error JSON from the AI
                if isinstance(data2, dict) and "error" in data2:
                    error_type = data2.get("error", "unknown_error")
                    error_message = data2.get("message", "Unknown error")

                    if error_type == "missing_input":
                        raise ParseError(
                            f"Input file not found: {error_message}. "
                            "Please ensure the file exists in the current directory and try again."
                        )
                    elif error_type == "unsupported_action":
                        raise ParseError(
                            f"Unsupported operation: {error_message}. "
                            "Please check the supported actions and try a different approach."
                        )
                    else:
                        raise ParseError(
                            f"AI model error: {error_message}. "
                            "Please try rephrasing your request or check if the operation is supported."
                        )

                intent2 = FfmpegIntent.model_validate(data2)
                logger.debug(f"Successfully parsed intent on retry: {intent2.action}")
                return intent2

            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed on retry: {json_err}")
                raise ParseError(
                    f"Failed to parse LLM response as JSON: {json_err}. "
                    "The AI model returned invalid JSON format. This could be due to: "
                    "(1) network issues - try increasing --timeout, "
                    "(2) model overload - try again in a moment, "
                    "(3) complex prompt - try simplifying your request."
                ) from json_err

            except ValidationError as val_err:
                logger.error(f"Schema validation failed on retry: {val_err}")
                raise ParseError(
                    f"Failed to validate parsed intent: {val_err}. "
                    "The AI model returned JSON that doesn't match expected format. "
                    "This could be due to: (1) unsupported operation - check supported actions, "
                    "(2) ambiguous prompt - be more specific about what you want to do, "
                    "(3) model issues - try --model gpt-4o for better accuracy."
                ) from val_err

            except ParseError:
                # Re-raise ParseError from provider (already has good error message)
                raise

            except OSError as io_err:
                logger.error(f"Network/IO error during retry: {io_err}")
                raise ParseError(
                    f"Network error during LLM request: {io_err}. "
                    "Please check your internet connection and try again."
                ) from io_err

    def _fix_common_issues(self, response: str) -> str:
        """Fix common issues in LLM responses before parsing.

        Applies regex-based fixes to common JSON formatting issues
        that LLMs sometimes produce.

        Args:
            response: Raw JSON response from LLM

        Returns:
            str: Fixed JSON response with corrected formatting
        """
        import re

        # Fix null values for array fields that should be empty arrays
        response = re.sub(r'"filters":\s*null', '"filters": []', response)
        response = re.sub(r'"extra_flags":\s*null', '"extra_flags": []', response)
        response = re.sub(r'"inputs":\s*null', '"inputs": []', response)

        # Fix missing array brackets for single values
        # Match patterns like "filters": "value" and convert to "filters": ["value"]
        response = re.sub(r'"filters":\s*"([^"]+)"', r'"filters": ["\1"]', response)
        response = re.sub(r'"extra_flags":\s*"([^"]+)"', r'"extra_flags": ["\1"]', response)

        return response
