"""Out-of-range --timeout values must be rejected (offline, fully mocked)."""

from unittest.mock import patch

import pytest
import typer

from ai_ffmpeg_cli.config import AppConfig
from ai_ffmpeg_cli.main import main


def _run_one_shot(timeout):
    """Run one-shot main with everything downstream mocked."""
    config = AppConfig(openai_api_key="test-key", dry_run=False)
    with (
        patch("ai_ffmpeg_cli.main.load_config", return_value=config),
        patch("ai_ffmpeg_cli.main.scan") as mock_scan,
        patch("ai_ffmpeg_cli.main._make_llm"),
    ):
        with pytest.raises(typer.Exit) as exc_info:
            main(
                None,
                prompt="convert test.mp4",
                yes=True,
                model=None,
                dry_run=None,
                timeout=timeout,
                verbose=False,
            )
    return exc_info.value.exit_code, mock_scan


def test_timeout_zero_is_rejected():
    """timeout=0 must exit 1 before any scan/LLM work happens."""
    code, mock_scan = _run_one_shot(0)
    assert code == 1
    mock_scan.assert_not_called()


def test_timeout_above_max_is_rejected():
    """timeout=99999 (documented max is 300) must exit 1."""
    code, mock_scan = _run_one_shot(99999)
    assert code == 1
    mock_scan.assert_not_called()
