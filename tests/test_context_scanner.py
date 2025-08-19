"""Tests for context_scanner.py file scanning functionality."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_ffmpeg_cli.context_scanner import _ffprobe_duration, scan


class TestFfprobeDuration:
    """Test ffprobe duration extraction."""

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    def test_ffprobe_not_available(self, mock_which):
        """Test when ffprobe is not available."""
        mock_which.return_value = None

        result = _ffprobe_duration(Path("test.mp4"))

        assert result is None
        mock_which.assert_called_once_with("ffprobe")

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    @patch("ai_ffmpeg_cli.context_scanner.subprocess.run")
    def test_ffprobe_success(self, mock_run, mock_which):
        """Test successful ffprobe duration extraction."""
        mock_which.return_value = "/usr/bin/ffprobe"

        # Mock successful ffprobe response
        mock_result = Mock()
        mock_result.stdout = json.dumps({"format": {"duration": "120.5"}})
        mock_run.return_value = mock_result

        result = _ffprobe_duration(Path("test.mp4"))

        assert result == 120.5
        mock_run.assert_called_once_with(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                "test.mp4",
            ],
            capture_output=True,
            check=True,
            text=True,
        )

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    @patch("ai_ffmpeg_cli.context_scanner.subprocess.run")
    def test_ffprobe_no_duration(self, mock_run, mock_which):
        """Test ffprobe response without duration."""
        mock_which.return_value = "/usr/bin/ffprobe"

        # Mock ffprobe response without duration
        mock_result = Mock()
        mock_result.stdout = json.dumps({"format": {}})
        mock_run.return_value = mock_result

        result = _ffprobe_duration(Path("test.mp4"))

        assert result is None

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    @patch("ai_ffmpeg_cli.context_scanner.subprocess.run")
    def test_ffprobe_invalid_duration(self, mock_run, mock_which):
        """Test ffprobe response with invalid duration."""
        mock_which.return_value = "/usr/bin/ffprobe"

        # Mock ffprobe response with invalid duration
        mock_result = Mock()
        mock_result.stdout = json.dumps({"format": {"duration": "invalid"}})
        mock_run.return_value = mock_result

        result = _ffprobe_duration(Path("test.mp4"))

        assert result is None

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    @patch("ai_ffmpeg_cli.context_scanner.subprocess.run")
    def test_ffprobe_subprocess_error(self, mock_run, mock_which):
        """Test ffprobe subprocess error."""
        mock_which.return_value = "/usr/bin/ffprobe"
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        result = _ffprobe_duration(Path("test.mp4"))

        assert result is None

    @patch("ai_ffmpeg_cli.context_scanner.shutil.which")
    @patch("ai_ffmpeg_cli.context_scanner.subprocess.run")
    def test_ffprobe_json_decode_error(self, mock_run, mock_which):
        """Test ffprobe with invalid JSON response."""
        mock_which.return_value = "/usr/bin/ffprobe"

        # Mock ffprobe response with invalid JSON
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        result = _ffprobe_duration(Path("test.mp4"))

        assert result is None


class TestScan:
    """Test directory scanning functionality."""

    def test_scan_default_directory(self, tmp_path):
        """Test scanning with default (current) directory."""
        # Create test files
        (tmp_path / "video.mp4").write_bytes(b"fake video")
        (tmp_path / "audio.mp3").write_bytes(b"fake audio")
        (tmp_path / "image.png").write_bytes(b"fake image")
        (tmp_path / "text.txt").write_bytes(b"text file")

        with patch("ai_ffmpeg_cli.context_scanner.Path.cwd", return_value=tmp_path):
            with patch(
                "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=120.0
            ):
                result = scan()

        assert result["cwd"] == str(tmp_path)
        video_names = [Path(v).name for v in result["videos"]]
        audio_names = [Path(a).name for a in result["audios"]]
        image_names = [Path(i).name for i in result["images"]]

        assert "video.mp4" in video_names
        assert "audio.mp3" in audio_names
        assert "image.png" in image_names

        # Check info structure
        assert len(result["info"]) == 2  # video and audio files
        video_info = next(
            info for info in result["info"] if "video.mp4" in info["path"]
        )
        assert video_info["duration"] == 120.0
        assert video_info["size"] > 0

    def test_scan_custom_directory(self, tmp_path):
        """Test scanning with custom directory."""
        # Create test files
        (tmp_path / "movie.mov").write_bytes(b"fake movie")
        (tmp_path / "song.wav").write_bytes(b"fake song")

        with patch(
            "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=None
        ):
            result = scan(cwd=tmp_path)

        assert result["cwd"] == str(tmp_path)
        video_names = [Path(v).name for v in result["videos"]]
        audio_names = [Path(a).name for a in result["audios"]]

        assert "movie.mov" in video_names
        assert "song.wav" in audio_names
        assert result["images"] == []

    @patch("ai_ffmpeg_cli.context_scanner.most_recent_file")
    def test_scan_with_most_recent_video(self, mock_most_recent, tmp_path):
        """Test scanning with most recent video detection."""
        # Create test files
        (tmp_path / "old.mp4").write_bytes(b"old video")
        (tmp_path / "new.mp4").write_bytes(b"new video")

        mock_most_recent.return_value = tmp_path / "new.mp4"

        with patch(
            "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=60.0
        ):
            result = scan(cwd=tmp_path)

        assert result["most_recent_video"] == str(tmp_path / "new.mp4")
        mock_most_recent.assert_called_once()

    @patch("ai_ffmpeg_cli.context_scanner.most_recent_file")
    def test_scan_no_most_recent_video(self, mock_most_recent, tmp_path):
        """Test scanning when no most recent video is found."""
        mock_most_recent.return_value = None

        result = scan(cwd=tmp_path)

        assert result["most_recent_video"] is None

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        result = scan(cwd=tmp_path)

        assert result["cwd"] == str(tmp_path)
        assert result["videos"] == []
        assert result["audios"] == []
        assert result["images"] == []
        assert result["most_recent_video"] is None
        assert result["info"] == []

    def test_scan_case_insensitive_extensions(self, tmp_path):
        """Test that file extension matching is case insensitive."""
        # Create files with uppercase extensions
        (tmp_path / "video.MP4").write_bytes(b"fake video")
        (tmp_path / "audio.MP3").write_bytes(b"fake audio")
        (tmp_path / "image.PNG").write_bytes(b"fake image")

        with patch(
            "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=None
        ):
            result = scan(cwd=tmp_path)

        video_names = [Path(v).name for v in result["videos"]]
        audio_names = [Path(a).name for a in result["audios"]]
        image_names = [Path(i).name for i in result["images"]]

        assert "video.MP4" in video_names
        assert "audio.MP3" in audio_names
        assert "image.PNG" in image_names

    def test_scan_various_media_formats(self, tmp_path):
        """Test scanning with various supported media formats."""
        # Video formats
        video_files = ["test.mp4", "test.mov", "test.mkv", "test.webm", "test.avi"]
        for filename in video_files:
            (tmp_path / filename).write_bytes(b"fake video")

        # Audio formats
        audio_files = ["test.mp3", "test.aac", "test.wav", "test.m4a", "test.flac"]
        for filename in audio_files:
            (tmp_path / filename).write_bytes(b"fake audio")

        # Image formats
        image_files = ["test.png", "test.jpg", "test.jpeg"]
        for filename in image_files:
            (tmp_path / filename).write_bytes(b"fake image")

        with patch(
            "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=None
        ):
            result = scan(cwd=tmp_path)

        # Extract filenames from full paths
        video_names = [Path(v).name for v in result["videos"]]
        audio_names = [Path(a).name for a in result["audios"]]
        image_names = [Path(i).name for i in result["images"]]

        # Check all formats are detected
        for filename in video_files:
            assert filename in video_names

        for filename in audio_files:
            assert filename in audio_names

        for filename in image_files:
            assert filename in image_names

    def test_scan_ignores_directories(self, tmp_path):
        """Test that scanning ignores subdirectories."""
        # Create a subdirectory with media files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "video.mp4").write_bytes(b"fake video")

        # Create file in main directory
        (tmp_path / "main.mp4").write_bytes(b"fake video")

        with patch(
            "ai_ffmpeg_cli.context_scanner._ffprobe_duration", return_value=None
        ):
            result = scan(cwd=tmp_path)

        # Extract filenames from full paths
        video_names = [Path(v).name for v in result["videos"]]

        # Should only find the main directory file
        assert len(result["videos"]) == 1
        assert "main.mp4" in video_names
        assert "video.mp4" not in video_names  # From subdirectory
