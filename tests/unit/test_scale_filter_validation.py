"""Test scale filter validation to ensure even dimensions for H.264/H.265 compatibility."""

from ai_ffmpeg_cli.intent_router import _validate_and_fix_scale_filter


class TestScaleFilterValidation:
    """Test scale filter validation and fixing."""

    def test_simple_dimensions_even(self):
        """Test that even dimensions are preserved."""
        result = _validate_and_fix_scale_filter("scale=1280:720")
        assert result == "scale=1280:720:force_original_aspect_ratio=decrease"

    def test_simple_dimensions_odd_width(self):
        """Test that odd width is corrected to even."""
        result = _validate_and_fix_scale_filter("scale=1281:720")
        assert result == "scale=1280:720:force_original_aspect_ratio=decrease"

    def test_simple_dimensions_odd_height(self):
        """Test that odd height is corrected to even."""
        result = _validate_and_fix_scale_filter("scale=1280:721")
        assert result == "scale=1280:720:force_original_aspect_ratio=decrease"

    def test_simple_dimensions_both_odd(self):
        """Test that both odd dimensions are corrected."""
        result = _validate_and_fix_scale_filter("scale=1281:721")
        assert result == "scale=1280:720:force_original_aspect_ratio=decrease"

    def test_complex_expression_with_force_original_aspect_ratio(self):
        """Test that complex expressions with force_original_aspect_ratio are preserved."""
        result = _validate_and_fix_scale_filter(
            "scale=iw*0.5:ih*0.5:force_original_aspect_ratio=decrease"
        )
        assert result == "scale=iw*0.5:ih*0.5:force_original_aspect_ratio=decrease"

    def test_complex_expression_without_force_original_aspect_ratio(self):
        """Test that complex expressions get force_original_aspect_ratio added."""
        result = _validate_and_fix_scale_filter("scale=iw*0.5:ih*0.5")
        assert result == "scale=iw*0.5:ih*0.5:force_original_aspect_ratio=decrease"

    def test_9_16_aspect_ratio_fix(self):
        """Test that 9:16 aspect ratio calculations are fixed to avoid odd dimensions."""
        result = _validate_and_fix_scale_filter("scale=ih*9/16:ih")
        assert result == "scale=iw:iw*16/9:force_original_aspect_ratio=decrease"

    def test_16_9_aspect_ratio_fix(self):
        """Test that 16:9 aspect ratio calculations are fixed to avoid odd dimensions."""
        result = _validate_and_fix_scale_filter("scale=iw*16/9:iw")
        assert result == "scale=iw:iw*9/16:force_original_aspect_ratio=decrease"

    def test_non_scale_filter_preserved(self):
        """Test that non-scale filters are preserved unchanged."""
        result = _validate_and_fix_scale_filter("fps=30")
        assert result == "fps=30"

    def test_empty_string_preserved(self):
        """Test that empty strings are preserved."""
        result = _validate_and_fix_scale_filter("")
        assert result == ""

    def test_none_preserved(self):
        """Test that None values are preserved."""
        result = _validate_and_fix_scale_filter(None)
        assert result is None

    def test_scale_with_additional_params(self):
        """Test scale filter with additional parameters."""
        result = _validate_and_fix_scale_filter("scale=1280:720:flags=lanczos")
        assert result == "scale=1280:720:flags=lanczos:force_original_aspect_ratio=decrease"

    def test_scale_with_odd_dimensions_and_params(self):
        """Test scale filter with odd dimensions and additional parameters."""
        result = _validate_and_fix_scale_filter("scale=1281:721:flags=lanczos")
        assert result == "scale=1280:720:flags=lanczos:force_original_aspect_ratio=decrease"
