from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from .errors import ParseError
from .nl_schema import FfmpegIntent

logger = logging.getLogger(__name__)


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

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, system: str, user: str, timeout: int) -> str:
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
        return rsp.choices[0].message.content or "{}"


class LLMClient:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def parse(
        self, nl_prompt: str, context: dict[str, Any], timeout: int | None = None
    ) -> FfmpegIntent:
        user_payload = json.dumps({"prompt": nl_prompt, "context": context})
        effective_timeout = 60 if timeout is None else timeout
        raw = self.provider.complete(SYSTEM_PROMPT, user_payload, timeout=effective_timeout)
        try:
            data = json.loads(raw)
            intent = FfmpegIntent.model_validate(data)
            return intent
        except (json.JSONDecodeError, ValidationError) as first_err:
            # one corrective pass
            logger.debug("Primary parse failed, attempting repair: %s", first_err)
            repair_prompt = "The previous output was invalid. Re-emit strictly valid JSON for FfmpegIntent only."
            raw2 = self.provider.complete(
                SYSTEM_PROMPT,
                repair_prompt + "\n" + user_payload,
                timeout=effective_timeout,
            )
            try:
                data2 = json.loads(raw2)
                intent2 = FfmpegIntent.model_validate(data2)
                return intent2
            except Exception as second_err:  # noqa: BLE001
                raise ParseError(
                    f"Failed to parse natural language prompt: {second_err}. "
                    "This could be due to: (1) network issues - try increasing --timeout, "
                    "(2) ambiguous prompt - be more specific, "
                    "(3) unsupported operation - check supported actions in --help, "
                    "or (4) model issues - try --model gpt-4o or gpt-4o-mini"
                ) from second_err
