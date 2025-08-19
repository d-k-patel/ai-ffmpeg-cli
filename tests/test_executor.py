from unittest.mock import patch

from ai_ffmpeg_cli.executor import run


def test_dry_run_returns_zero():
    cmds = [["ffmpeg", "-i", "in.mp4", "out.mp4"]]
    assert run(cmds, confirm=True, dry_run=True) == 0


@patch("subprocess.run")
def test_run_executes_when_confirmed(mock_run):
    mock_run.return_value.returncode = 0
    cmds = [["ffmpeg", "-i", "in.mp4", "out.mp4"]]
    assert run(cmds, confirm=True, dry_run=False) == 0
    assert mock_run.called
