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
    def complete(self, system: str, user: str, timeout: int) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
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
        """Complete chat request with error handling and retries."""
        try:
            logger.debug(f"Making OpenAI API request with model: {self.model}, timeout: {timeout}s")

            rsp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0,
                response_format={"type": "json_object"},
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
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def parse(
        self, nl_prompt: str, context: dict[str, Any], timeout: int | None = None
    ) -> FfmpegIntent:
        """Parse natural language prompt into FfmpegIntent with retry logic.

        Args:
            nl_prompt: Natural language prompt from user
            context: File context information
            timeout: Request timeout in seconds

        Returns:
            FfmpegIntent: Parsed intent object

        Raises:
            ParseError: If parsing fails after retry attempts
        """
        # Sanitize user input first
        from .io_utils import sanitize_user_input

        sanitized_prompt = sanitize_user_input(nl_prompt)

        if not sanitized_prompt.strip():
            raise ParseError(
                "Empty or invalid prompt provided. Please provide a clear description of what you want to do."
            )

        user_payload = json.dumps({"prompt": sanitized_prompt, "context": context})
        effective_timeout = 60 if timeout is None else timeout

        logger.debug(f"Parsing prompt with timeout: {effective_timeout}s")

        # First attempt
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
