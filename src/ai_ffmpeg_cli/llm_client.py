"""LLM client for natural language to ffmpeg intent translation.

This module provides the interface between natural language prompts and
structured ffmpeg intents using Large Language Models (LLMs). It handles
API communication, error handling, retry logic, and response validation.

Key features:
- OpenAI API integration with comprehensive error handling
- Automatic retry with corrective prompts for parsing failures
- Input sanitization and security logging
- Mock responses for testing and development
- Structured JSON response validation

Security considerations:
- API keys are never logged
- User input is sanitized before processing
- Error messages are sanitized to prevent information leakage
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from .errors import ParseError
from .nl_schema import FfmpegIntent
from .security import create_secure_logger
from .security import sanitize_error_message

logger = create_secure_logger(__name__)


SYSTEM_PROMPT = (
    "You are an expert assistant that translates natural language into ffmpeg intents. "
    "Respond ONLY with JSON matching the FfmpegIntent schema. Fields: action, inputs, output, "
    "video_codec, audio_codec, filters, start, end, duration, scale, bitrate, crf, overlay_path, "
    "overlay_xy, fps, glob, extra_flags. Use defaults: convert uses libx264+aac; 720p->scale=1280:720, "
    "1080p->1920:1080; compression uses libx265 with crf=28. If unsupported, reply with "
    '{"error": "unsupported_action", "message": "..."}.'
)


class LLMProvider:
    """Abstract base class for LLM providers.

    Defines the interface for different LLM services. Implementations
    should handle API communication, authentication, and response formatting.
    """
    def complete(self, system: str, user: str, timeout: int) -> str:  # pragma: no cover - interface
        """Complete a chat request with system and user messages.

        Args:
            system: System prompt defining the assistant's role
            user: User message to process
            timeout: Request timeout in seconds

        Returns:
            str: Raw response from the LLM

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for LLM completions.

    Handles communication with OpenAI's chat completion API, including
    authentication, error handling, and response processing.
    """
    def __init__(self, api_key: str, model: str) -> None:
        """Initialize OpenAI provider with API credentials.

        Args:
            api_key: OpenAI API key for authentication
            model: Model name to use for completions (e.g., gpt-4o, gpt-3.5-turbo)

        Raises:
            Exception: If client initialization fails
        """
        from openai import OpenAI  # lazy import for testability

        # Never log the actual API key - only model and status
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
        """Complete chat request with comprehensive error handling.

        Makes a chat completion request to OpenAI with proper error handling
        for authentication, rate limiting, timeouts, and API errors.

        Args:
            system: System prompt defining assistant behavior
            user: User message to process
            timeout: Request timeout in seconds

        Returns:
            str: JSON response from OpenAI

        Raises:
            ParseError: For authentication, rate limiting, timeout, or API errors
        """
        try:
            logger.debug(f"Making OpenAI API request with model: {self.model}, timeout: {timeout}s")

            rsp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0,  # Deterministic responses for consistent parsing
                response_format={"type": "json_object"},  # Ensure JSON output
                timeout=timeout,
            )

            content = rsp.choices[0].message.content or "{}"
            logger.debug(f"Received response length: {len(content)} characters")
            return content

        except Exception as e:
            # Import specific exception types for better error handling
            try:
                from openai import APIError
                from openai import APITimeoutError
                from openai import AuthenticationError
                from openai import RateLimitError

                if isinstance(e, AuthenticationError):
                    # Authentication failed - provide clear guidance
                    logger.error("OpenAI authentication failed - check your API key")
                    raise ParseError(
                        "OpenAI authentication failed. Please check your API key is correct "
                        "and has sufficient credits. Set OPENAI_API_KEY environment variable "
                        "or use --model to specify a different model."
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
                # Fallback for older openai versions without specific exception types
                pass

            # Generic error handling for unknown exceptions
            sanitized_error = sanitize_error_message(str(e))
            logger.error(f"Unexpected error during OpenAI request: {sanitized_error}")
            raise ParseError(
                f"Failed to get response from OpenAI: {sanitized_error}. "
                "Please check your internet connection and try again."
            ) from e

    def _get_mock_response(self, _system: str, user: str) -> str:
        """Generate a mock response for testing purposes.

        Provides deterministic responses for common test scenarios without
        requiring actual API calls. Used for development and testing.

        Args:
            _system: System prompt (unused in mock)
            user: User message to generate mock response for

        Returns:
            str: JSON response matching FfmpegIntent schema
        """
        import json

        # Parse the user input to understand the request
        try:
            user_data = json.loads(user)
            prompt = user_data.get("prompt", "").lower()

            # Generate appropriate mock response based on the prompt content
            if "convert" in prompt and "720p" in prompt:
                return json.dumps(
                    {
                        "action": "convert",
                        "inputs": ["test.mp4"],
                        "scale": "1280:720",
                        "video_codec": "libx264",
                        "audio_codec": "aac",
                    }
                )
            elif "extract" in prompt and "audio" in prompt:
                return json.dumps({"action": "extract_audio", "inputs": ["test.mp4"]})
            elif "trim" in prompt:
                return json.dumps(
                    {
                        "action": "trim",
                        "inputs": ["test.mp4"],
                        "start": "00:00:00",
                        "duration": 30.0,
                    }
                )
            elif "thumbnail" in prompt:
                return json.dumps(
                    {"action": "thumbnail", "inputs": ["test.mp4"], "start": "00:00:10"}
                )
            elif "compress" in prompt:
                return json.dumps({"action": "compress", "inputs": ["test.mp4"], "crf": 28})
            else:
                # Default response for unknown requests
                return json.dumps(
                    {
                        "action": "convert",
                        "inputs": ["test.mp4"],
                        "video_codec": "libx264",
                        "audio_codec": "aac",
                    }
                )
        except (json.JSONDecodeError, KeyError):
            # Fallback response if user input parsing fails
            return json.dumps(
                {
                    "action": "convert",
                    "inputs": ["test.mp4"],
                    "video_codec": "libx264",
                    "audio_codec": "aac",
                }
            )


class LLMClient:
    """High-level LLM client for natural language parsing.

    Provides a unified interface for parsing natural language prompts into
    structured ffmpeg intents, with retry logic and comprehensive error handling.
    """
    def __init__(self, provider: LLMProvider) -> None:
        """Initialize client with a specific LLM provider.

        Args:
            provider: LLM provider implementation (e.g., OpenAIProvider)
        """
        self.provider = provider

    def parse(
        self, nl_prompt: str, context: dict[str, Any], timeout: int | None = None
    ) -> FfmpegIntent:
        """Parse natural language prompt into FfmpegIntent with retry logic.

        Converts user natural language into structured ffmpeg intents using
        the configured LLM provider. Includes automatic retry with corrective
        prompts for parsing failures.

        Args:
            nl_prompt: Natural language prompt from user
            context: File context information (available files, etc.)
            timeout: Request timeout in seconds (defaults to 60)

        Returns:
            FfmpegIntent: Parsed and validated intent object

        Raises:
            ParseError: If parsing fails after retry attempts, with detailed error guidance
        """
        # Sanitize user input first to prevent injection attacks
        from .io_utils import sanitize_user_input

        sanitized_prompt = sanitize_user_input(nl_prompt)

        if not sanitized_prompt.strip():
            raise ParseError(
                "Empty or invalid prompt provided. Please provide a clear description of what you want to do."
            )

        # Prepare payload with prompt and context for LLM
        user_payload = json.dumps({"prompt": sanitized_prompt, "context": context})
        effective_timeout = 60 if timeout is None else timeout

        logger.debug(f"Parsing prompt with timeout: {effective_timeout}s")

        # First attempt with original prompt
        try:
            raw = self.provider.complete(SYSTEM_PROMPT, user_payload, timeout=effective_timeout)
            logger.debug(f"Received raw response: {len(raw)} chars")

            data = json.loads(raw)
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
