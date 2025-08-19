"""Comprehensive tests for executor.py command execution."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from ai_ffmpeg_cli.executor import (
    _check_overwrite_protection,
    _extract_output_path,
    _format_command,
    preview,
    run,
)
from ai_ffmpeg_cli.errors import ExecError


class TestFormatCommand:
    """Test command formatting."""

    def test_format_simple_command(self):
        """Test formatting simple command."""
        cmd = ["ffmpeg", "-i", "input.mp4", "output.mp4"]
        result = _format_command(cmd)
        assert result == "ffmpeg -i input.mp4 output.mp4"

    def test_format_complex_command(self):
        """Test formatting complex command with many arguments."""
        cmd = [
            "ffmpeg",
            "-ss",
            "00:00:10",
            "-i",
            "input.mp4",
            "-vf",
            "scale=1280:720",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-y",
            "output.mp4",
        ]
        result = _format_command(cmd)
        expected = "ffmpeg -ss 00:00:10 -i input.mp4 -vf scale=1280:720 -c:v libx264 -c:a aac -y output.mp4"
        assert result == expected

    def test_format_empty_command(self):
        """Test formatting empty command."""
        result = _format_command([])
        assert result == ""

    def test_format_single_argument(self):
        """Test formatting command with single argument."""
        result = _format_command(["ffmpeg"])
        assert result == "ffmpeg"


class TestExtractOutputPath:
    """Test output path extraction."""

    def test_extract_output_path_normal(self):
        """Test extracting output path from normal command."""
        cmd = ["ffmpeg", "-i", "input.mp4", "output.mp4"]
        result = _extract_output_path(cmd)
        assert result == Path("output.mp4")

    def test_extract_output_path_with_flags(self):
        """Test extracting output path with many flags."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            "input.mp4",
            "-vf",
            "scale=720:480",
            "-c:v",
            "libx264",
            "final_output.mp4",
        ]
        result = _extract_output_path(cmd)
        assert result == Path("final_output.mp4")

    def test_extract_output_path_empty_command(self):
        """Test extracting output path from empty command."""
        result = _extract_output_path([])
        assert result is None

    def test_extract_output_path_single_argument(self):
        """Test extracting output path from single argument command."""
        result = _extract_output_path(["ffmpeg"])
        assert result is None

    def test_extract_output_path_absolute(self):
        """Test extracting absolute output path."""
        cmd = ["ffmpeg", "-i", "input.mp4", "/path/to/output.mp4"]
        result = _extract_output_path(cmd)
        assert result == Path("/path/to/output.mp4")


class TestCheckOverwriteProtection:
    """Test overwrite protection logic."""

    def test_no_existing_files(self):
        """Test when no output files exist."""
        commands = [["ffmpeg", "-i", "input.mp4", "nonexistent.mp4"]]

        with patch("ai_ffmpeg_cli.executor.Path.exists", return_value=False):
            result = _check_overwrite_protection(commands, assume_yes=False)

        assert result is True

    def test_assume_yes_with_existing_files(self, tmp_path):
        """Test assume_yes=True skips confirmation even with existing files."""
        output_file = tmp_path / "existing.mp4"
        output_file.write_text("existing content")

        commands = [["ffmpeg", "-i", "input.mp4", str(output_file)]]

        result = _check_overwrite_protection(commands, assume_yes=True)

        assert result is True

    @patch("ai_ffmpeg_cli.executor.confirm_prompt")
    @patch("ai_ffmpeg_cli.executor.Console")
    def test_existing_files_confirm_yes(self, mock_console, mock_confirm, tmp_path):
        """Test with existing files and user confirms overwrite."""
        output_file = tmp_path / "existing.mp4"
        output_file.write_text("existing content")

        commands = [["ffmpeg", "-i", "input.mp4", str(output_file)]]
        mock_confirm.return_value = True

        result = _check_overwrite_protection(commands, assume_yes=False)

        assert result is True
        mock_confirm.assert_called_once_with(
            "Continue and overwrite these files?", default_yes=False, assume_yes=False
        )

    @patch("ai_ffmpeg_cli.executor.confirm_prompt")
    @patch("ai_ffmpeg_cli.executor.Console")
    def test_existing_files_confirm_no(self, mock_console, mock_confirm, tmp_path):
        """Test with existing files and user declines overwrite."""
        output_file = tmp_path / "existing.mp4"
        output_file.write_text("existing content")

        commands = [["ffmpeg", "-i", "input.mp4", str(output_file)]]
        mock_confirm.return_value = False

        result = _check_overwrite_protection(commands, assume_yes=False)

        assert result is False

    @patch("ai_ffmpeg_cli.executor.confirm_prompt")
    @patch("ai_ffmpeg_cli.executor.Console")
    def test_multiple_existing_files(self, mock_console, mock_confirm, tmp_path):
        """Test with multiple existing files."""
        output1 = tmp_path / "existing1.mp4"
        output2 = tmp_path / "existing2.mp4"
        output1.write_text("content1")
        output2.write_text("content2")

        commands = [
            ["ffmpeg", "-i", "input1.mp4", str(output1)],
            ["ffmpeg", "-i", "input2.mp4", str(output2)],
        ]
        mock_confirm.return_value = True

        result = _check_overwrite_protection(commands, assume_yes=False)

        assert result is True
        # Should show both files in warning
        mock_console.return_value.print.assert_called()

    def test_mixed_existing_nonexisting_files(self, tmp_path):
        """Test with mix of existing and non-existing files."""
        existing_file = tmp_path / "existing.mp4"
        existing_file.write_text("content")

        commands = [
            ["ffmpeg", "-i", "input1.mp4", str(existing_file)],
            ["ffmpeg", "-i", "input2.mp4", str(tmp_path / "nonexistent.mp4")],
        ]

        with patch(
            "ai_ffmpeg_cli.executor.confirm_prompt", return_value=True
        ) as mock_confirm:
            with patch("ai_ffmpeg_cli.executor.Console"):
                result = _check_overwrite_protection(commands, assume_yes=False)

        assert result is True
        # Should still prompt because one file exists
        mock_confirm.assert_called_once()


class TestPreview:
    """Test command preview functionality."""

    @patch("ai_ffmpeg_cli.executor.Console")
    def test_preview_single_command(self, mock_console):
        """Test previewing single command."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]

        preview(commands)

        mock_console.assert_called_once()
        console_instance = mock_console.return_value
        console_instance.print.assert_called_once()

    @patch("ai_ffmpeg_cli.executor.Console")
    def test_preview_multiple_commands(self, mock_console):
        """Test previewing multiple commands."""
        commands = [
            ["ffmpeg", "-i", "input1.mp4", "output1.mp4"],
            ["ffmpeg", "-i", "input2.mp4", "output2.mp4"],
            ["ffmpeg", "-i", "input3.mp4", "output3.mp4"],
        ]

        preview(commands)

        mock_console.assert_called_once()
        console_instance = mock_console.return_value
        console_instance.print.assert_called_once()

        # Table should be created with correct number of rows
        table_arg = console_instance.print.call_args[0][0]
        # Would need to inspect table structure in real implementation


class TestRun:
    """Test command execution functionality."""

    @patch("ai_ffmpeg_cli.executor.preview")
    def test_run_dry_run_mode(self, mock_preview):
        """Test run in dry-run mode."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]

        result = run(commands, confirm=True, dry_run=True, show_preview=True)

        assert result == 0
        mock_preview.assert_called_once_with(commands)

    @patch("ai_ffmpeg_cli.executor.preview")
    def test_run_not_confirmed(self, mock_preview):
        """Test run when not confirmed."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]

        result = run(commands, confirm=False, dry_run=False, show_preview=True)

        assert result == 0
        mock_preview.assert_called_once_with(commands)

    @patch("ai_ffmpeg_cli.executor.preview")
    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    @patch("ai_ffmpeg_cli.executor.subprocess.run")
    def test_run_successful_execution(
        self, mock_subprocess, mock_overwrite, mock_preview
    ):
        """Test successful command execution."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]
        mock_overwrite.return_value = True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = run(
            commands, confirm=True, dry_run=False, show_preview=True, assume_yes=False
        )

        assert result == 0
        mock_subprocess.assert_called_once_with(commands[0], check=True)
        mock_overwrite.assert_called_once()

    @patch("ai_ffmpeg_cli.executor.preview")
    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    def test_run_overwrite_cancelled(self, mock_overwrite, mock_preview):
        """Test when user cancels due to overwrite protection."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]
        mock_overwrite.return_value = False

        result = run(
            commands, confirm=True, dry_run=False, show_preview=True, assume_yes=False
        )

        assert result == 1  # Cancelled

    @patch("ai_ffmpeg_cli.executor.preview")
    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    @patch("ai_ffmpeg_cli.executor.subprocess.run")
    def test_run_command_failure(self, mock_subprocess, mock_overwrite, mock_preview):
        """Test command execution failure."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]
        mock_overwrite.return_value = True

        # Mock command failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        with pytest.raises(ExecError, match="ffmpeg execution failed"):
            run(
                commands,
                confirm=True,
                dry_run=False,
                show_preview=True,
                assume_yes=False,
            )

    @patch("ai_ffmpeg_cli.executor.preview")
    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    @patch("ai_ffmpeg_cli.executor.subprocess.run")
    def test_run_multiple_commands(self, mock_subprocess, mock_overwrite, mock_preview):
        """Test execution of multiple commands."""
        commands = [
            ["ffmpeg", "-i", "input1.mp4", "output1.mp4"],
            ["ffmpeg", "-i", "input2.mp4", "output2.mp4"],
        ]
        mock_overwrite.return_value = True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = run(
            commands, confirm=True, dry_run=False, show_preview=True, assume_yes=False
        )

        assert result == 0
        assert mock_subprocess.call_count == 2
        mock_subprocess.assert_has_calls(
            [call(commands[0], check=True), call(commands[1], check=True)]
        )

    @patch("ai_ffmpeg_cli.executor.preview")
    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    @patch("ai_ffmpeg_cli.executor.subprocess.run")
    def test_run_second_command_fails(
        self, mock_subprocess, mock_overwrite, mock_preview
    ):
        """Test when second command fails."""
        commands = [
            ["ffmpeg", "-i", "input1.mp4", "output1.mp4"],
            ["ffmpeg", "-i", "input2.mp4", "output2.mp4"],
        ]
        mock_overwrite.return_value = True

        # First command succeeds, second fails
        mock_results = [Mock(), None]  # Second will raise exception
        mock_results[0].returncode = 0
        mock_subprocess.side_effect = [
            mock_results[0],
            subprocess.CalledProcessError(1, "ffmpeg"),
        ]

        with pytest.raises(ExecError):
            run(
                commands,
                confirm=True,
                dry_run=False,
                show_preview=True,
                assume_yes=False,
            )

        # Should have called both commands before failing
        assert mock_subprocess.call_count == 2

    @patch("ai_ffmpeg_cli.executor.preview")
    def test_run_no_preview(self, mock_preview):
        """Test run without showing preview."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]

        result = run(commands, confirm=True, dry_run=True, show_preview=False)

        assert result == 0
        mock_preview.assert_not_called()

    @patch("ai_ffmpeg_cli.executor._check_overwrite_protection")
    @patch("ai_ffmpeg_cli.executor.subprocess.run")
    def test_run_with_assume_yes(self, mock_subprocess, mock_overwrite):
        """Test run with assume_yes parameter."""
        commands = [["ffmpeg", "-i", "input.mp4", "output.mp4"]]
        mock_overwrite.return_value = True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = run(
            commands, confirm=True, dry_run=False, show_preview=False, assume_yes=True
        )

        assert result == 0
        mock_overwrite.assert_called_once_with(
            commands, True
        )  # assume_yes passed through
