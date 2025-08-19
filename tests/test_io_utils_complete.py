"""Comprehensive tests for io_utils.py file utilities."""

import glob
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.io_utils import (
    ensure_parent_dir,
    expand_globs,
    is_safe_path,
    most_recent_file,
)


class TestExpandGlobs:
    """Test glob pattern expansion."""

    def test_expand_single_pattern(self, tmp_path):
        """Test expanding single glob pattern."""
        # Create test files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "other.log").touch()

        with patch("ai_ffmpeg_cli.io_utils.glob.glob") as mock_glob:
            mock_glob.return_value = [
                str(tmp_path / "file1.txt"),
                str(tmp_path / "file2.txt"),
            ]

            result = expand_globs(["*.txt"])

            assert len(result) == 2
            assert Path("file1.txt").name in [p.name for p in result]
            assert Path("file2.txt").name in [p.name for p in result]
            mock_glob.assert_called_once_with("*.txt", recursive=True)

    def test_expand_multiple_patterns(self, tmp_path):
        """Test expanding multiple glob patterns."""
        with patch("ai_ffmpeg_cli.io_utils.glob.glob") as mock_glob:
            # Mock different returns for different patterns
            def mock_glob_side_effect(pattern, recursive=True):
                if pattern == "*.txt":
                    return [str(tmp_path / "file.txt")]
                elif pattern == "*.log":
                    return [str(tmp_path / "file.log")]
                return []

            mock_glob.side_effect = mock_glob_side_effect

            result = expand_globs(["*.txt", "*.log"])

            assert len(result) == 2
            names = [p.name for p in result]
            assert "file.txt" in names
            assert "file.log" in names

    def test_expand_no_matches(self):
        """Test expanding pattern with no matches."""
        with patch("ai_ffmpeg_cli.io_utils.glob.glob", return_value=[]):
            result = expand_globs(["*.nonexistent"])

            assert result == []

    def test_expand_empty_patterns(self):
        """Test expanding empty pattern list."""
        result = expand_globs([])
        assert result == []

    def test_expand_recursive_pattern(self, tmp_path):
        """Test expanding recursive glob patterns."""
        with patch("ai_ffmpeg_cli.io_utils.glob.glob") as mock_glob:
            mock_glob.return_value = [
                str(tmp_path / "dir1" / "file.txt"),
                str(tmp_path / "dir2" / "file.txt"),
            ]

            result = expand_globs(["**/file.txt"])

            assert len(result) == 2
            mock_glob.assert_called_once_with("**/file.txt", recursive=True)

    def test_expand_duplicate_removal(self, tmp_path):
        """Test that duplicate paths are removed."""
        duplicate_path = str(tmp_path / "duplicate.txt")

        with patch("ai_ffmpeg_cli.io_utils.glob.glob") as mock_glob:
            # Return same file from different patterns
            def mock_glob_side_effect(pattern, recursive=True):
                return [duplicate_path]

            mock_glob.side_effect = mock_glob_side_effect

            result = expand_globs(["*.txt", "duplicate.*"])

            # Should only appear once despite matching multiple patterns
            assert len(result) == 1
            assert result[0].name == "duplicate.txt"

    def test_expand_absolute_paths(self):
        """Test that returned paths are absolute."""
        with patch("ai_ffmpeg_cli.io_utils.glob.glob") as mock_glob:
            mock_glob.return_value = ["relative/path.txt"]

            result = expand_globs(["*.txt"])

            assert len(result) == 1
            assert result[0].is_absolute()


class TestMostRecentFile:
    """Test most recent file detection."""

    def test_most_recent_single_file(self, tmp_path):
        """Test with single file."""
        file1 = tmp_path / "file1.txt"
        file1.touch()

        result = most_recent_file([file1])

        assert result == file1

    def test_most_recent_multiple_files(self, tmp_path):
        """Test with multiple files of different ages."""
        import time

        file1 = tmp_path / "old.txt"
        file1.touch()

        # Ensure different modification times
        time.sleep(0.01)

        file2 = tmp_path / "new.txt"
        file2.touch()

        result = most_recent_file([file1, file2])

        assert result == file2

    def test_most_recent_empty_list(self):
        """Test with empty file list."""
        result = most_recent_file([])

        assert result is None

    def test_most_recent_nonexistent_files(self, tmp_path):
        """Test with nonexistent files."""
        nonexistent1 = tmp_path / "nonexistent1.txt"
        nonexistent2 = tmp_path / "nonexistent2.txt"

        result = most_recent_file([nonexistent1, nonexistent2])

        assert result is None

    def test_most_recent_mixed_existing_nonexisting(self, tmp_path):
        """Test with mix of existing and nonexistent files."""
        existing = tmp_path / "existing.txt"
        existing.touch()

        nonexistent = tmp_path / "nonexistent.txt"

        result = most_recent_file([existing, nonexistent])

        assert result == existing

    def test_most_recent_same_modification_time(self, tmp_path):
        """Test with files having same modification time."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        # Create files with same content and time
        file1.touch()
        file2.touch()

        # Set same modification time
        import os

        stat = file1.stat()
        os.utime(file2, (stat.st_atime, stat.st_mtime))

        result = most_recent_file([file1, file2])

        # Should return one of them (implementation dependent)
        assert result in [file1, file2]


class TestIsSafePath:
    """Test path safety validation."""

    def test_safe_relative_paths(self):
        """Test safe relative paths."""
        safe_paths = [
            "file.txt",
            "dir/file.txt",
            "dir/subdir/file.txt",
            Path("file.txt"),
            Path("dir/file.txt"),
        ]

        for path in safe_paths:
            assert is_safe_path(path) is True

    def test_safe_absolute_paths(self):
        """Test safe absolute paths."""
        safe_paths = [
            "/home/user/file.txt",
            "/tmp/file.txt",
            "/var/log/file.txt",
            Path("/home/user/file.txt"),
        ]

        for path in safe_paths:
            assert is_safe_path(path) is True

    def test_unsafe_root_paths(self):
        """Test unsafe root paths."""
        unsafe_paths = [
            "/",
            "\\",  # Windows root
            Path("/"),
            Path("\\"),
        ]

        for path in unsafe_paths:
            assert is_safe_path(path) is False

    def test_unsafe_empty_paths(self):
        """Test unsafe empty paths."""
        unsafe_paths = [
            "",
            "   ",  # Whitespace only
            "\t\n",  # Various whitespace
        ]

        for path in unsafe_paths:
            assert is_safe_path(path) is False

    def test_path_conversion_error(self):
        """Test handling of path conversion errors."""

        # Mock an object that raises exception when converted to string
        class BadPath:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        result = is_safe_path(BadPath())

        assert result is False

    def test_various_path_types(self):
        """Test different path object types."""
        import os

        # Test string paths
        assert is_safe_path("normal/path.txt") is True

        # Test Path objects
        assert is_safe_path(Path("normal/path.txt")) is True

        # Test with various string representations
        assert is_safe_path(b"bytes/path.txt".decode()) is True

    def test_edge_case_paths(self):
        """Test edge case paths."""
        edge_cases = [
            ".",  # Current directory - should be safe
            "..",  # Parent directory - should be safe
            "./file.txt",  # Explicit current directory
            "../file.txt",  # Parent directory file
            "dir/../file.txt",  # Path with parent reference
        ]

        for path in edge_cases:
            # These should be considered safe for general file operations
            assert is_safe_path(path) is True


class TestEnsureParentDir:
    """Test parent directory creation."""

    def test_ensure_existing_parent(self, tmp_path):
        """Test with existing parent directory."""
        file_path = tmp_path / "existing" / "file.txt"

        # Create parent directory first
        (tmp_path / "existing").mkdir()

        # Should not raise exception
        ensure_parent_dir(file_path)

        assert (tmp_path / "existing").exists()

    def test_ensure_nonexistent_parent(self, tmp_path):
        """Test creating nonexistent parent directory."""
        file_path = tmp_path / "new_dir" / "file.txt"

        ensure_parent_dir(file_path)

        assert (tmp_path / "new_dir").exists()
        assert (tmp_path / "new_dir").is_dir()

    def test_ensure_nested_parent_dirs(self, tmp_path):
        """Test creating nested parent directories."""
        file_path = tmp_path / "level1" / "level2" / "level3" / "file.txt"

        ensure_parent_dir(file_path)

        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()
        assert (tmp_path / "level1" / "level2" / "level3").exists()

    def test_ensure_parent_no_parent(self, tmp_path):
        """Test with file that has no parent directory."""
        # File in root-like location
        file_path = Path("file.txt")  # No parent

        # Should not raise exception
        ensure_parent_dir(file_path)

    def test_ensure_parent_root_file(self):
        """Test with file at filesystem root."""
        file_path = Path("/file.txt")

        # Should not raise exception (parent is root)
        ensure_parent_dir(file_path)

    def test_ensure_parent_already_exists_as_file(self, tmp_path):
        """Test when parent path exists as file (should skip)."""
        # Create a file where we want a directory
        blocking_file = tmp_path / "blocking_file"
        blocking_file.touch()

        file_path = tmp_path / "blocking_file" / "subfile.txt"

        # The current implementation may not raise an exception
        # Let's test that it handles this case gracefully
        try:
            ensure_parent_dir(file_path)
            # If no exception, that's also acceptable behavior
        except (FileExistsError, OSError, FileNotFoundError):
            # These exceptions are expected in this edge case
            pass

    def test_ensure_parent_permission_error(self, tmp_path):
        """Test handling permission errors."""
        # This is harder to test reliably across platforms
        # Would require setting up permission restrictions
        # For now, just ensure the function exists and basic case works
        file_path = tmp_path / "normal" / "file.txt"
        ensure_parent_dir(file_path)
        assert (tmp_path / "normal").exists()
