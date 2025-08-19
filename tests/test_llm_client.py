import json

from ai_ffmpeg_cli.llm_client import LLMClient
from ai_ffmpeg_cli.llm_client import LLMProvider
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


class DummyProvider(LLMProvider):
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = 0

    def complete(self, system: str, user: str, timeout: int) -> str:
        idx = min(self.calls, len(self.payloads) - 1)
        self.calls += 1
        return self.payloads[idx]


def test_llm_parse_success():
    intent = {
        "action": "convert",
        "inputs": ["input.mov"],
    }
    provider = DummyProvider([json.dumps(intent)])
    client = LLMClient(provider)
    parsed = client.parse("convert", {"cwd": "."})
    assert isinstance(parsed, FfmpegIntent)
    assert parsed.action == Action.convert


def test_llm_parse_repair_loop():
    bad = "not json"
    good = json.dumps({"action": "extract_audio", "inputs": ["demo.mp4"]})
    provider = DummyProvider([bad, good])
    client = LLMClient(provider)
    parsed = client.parse("extract", {})
    assert parsed.action == Action.extract_audio
