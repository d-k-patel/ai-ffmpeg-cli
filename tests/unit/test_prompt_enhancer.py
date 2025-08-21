"""Test prompt enhancement utilities."""

from ai_ffmpeg_cli.prompt_enhancer import PromptEnhancer
from ai_ffmpeg_cli.prompt_enhancer import enhance_user_prompt
from ai_ffmpeg_cli.prompt_enhancer import get_prompt_suggestions


class TestPromptEnhancer:
    """Test the PromptEnhancer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhancer = PromptEnhancer()
        self.sample_context = {
            "videos": ["/path/to/video.mp4"],
            "audios": ["/path/to/audio.mp3"],
            "subtitle_files": ["/path/to/subtitle.srt"],
        }

    def test_aspect_ratio_patterns(self):
        """Test aspect ratio pattern enhancements."""
        test_cases = [
            ("make 16:9 aspect ratio", "convert to 16:9 aspect ratio"),
            ("resize to 9:16", "9:16"),
            ("scale to 1:1 aspect ratio", "convert to 1:1 aspect ratio"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_social_media_patterns(self):
        """Test social media platform pattern enhancements."""
        test_cases = [
            (
                "for Instagram Reels",
                "for Instagram Reels (9:16 aspect ratio, 1080x1920)",
            ),
            ("for TikTok", "for TikTok (9:16 aspect ratio, 1080x1920)"),
            ("for YouTube Shorts", "for YouTube Shorts (9:16 aspect ratio, 1080x1920)"),
            ("for YouTube videos", "for YouTube videos (16:9 aspect ratio, 1920x1080)"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_quality_patterns(self):
        """Test quality-related pattern enhancements."""
        test_cases = [
            ("high quality", "high quality (lower CRF value)"),
            ("small file size", "small file size (higher CRF value)"),
            ("compress", "compress for smaller file size"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_audio_patterns(self):
        """Test audio-related pattern enhancements."""
        test_cases = [
            ("remove audio", "remove audio track"),
            ("extract audio", "extract audio to separate file"),
            ("mute", "remove audio track"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_subtitle_patterns(self):
        """Test subtitle-related pattern enhancements."""
        test_cases = [
            ("add captions", "burn in subtitles"),
            ("burn subtitles", "burn in subtitles"),
            ("hardcode subtitles", "burn in subtitles"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_common_shortcuts(self):
        """Test common shortcut pattern enhancements."""
        test_cases = [
            ("make it vertical", "convert to 9:16 aspect ratio (vertical)"),
            ("make it horizontal", "convert to 16:9 aspect ratio (horizontal)"),
            ("make it square", "convert to 1:1 aspect ratio (square)"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_context_enhancements(self):
        """Test context-aware enhancements."""
        # Test with single video file
        enhanced = self.enhancer.enhance_prompt("convert video", self.sample_context)
        assert "using video file: /path/to/video.mp4" in enhanced

        # Test with subtitle mention
        enhanced = self.enhancer.enhance_prompt("add subtitles", self.sample_context)
        assert "using subtitle file: /path/to/subtitle.srt" in enhanced

        # Test with multiple files
        multi_context = {
            "videos": ["/path/to/video1.mp4", "/path/to/video2.mp4"],
            "subtitle_files": ["/path/to/sub1.srt", "/path/to/sub2.srt"],
        }
        enhanced = self.enhancer.enhance_prompt("convert video", multi_context)
        assert "using one of 2 available video files" in enhanced

    def test_missing_details_enhancements(self):
        """Test adding missing details."""
        # Test aspect ratio without resolution
        enhanced = self.enhancer.enhance_prompt("convert to 9:16 aspect ratio", {})
        assert "suggest 1080x1920 resolution" in enhanced

        # Test quality without specific settings
        enhanced = self.enhancer.enhance_prompt("high quality", {})
        assert "high quality (lower CRF value)" in enhanced

    def test_term_normalization(self):
        """Test term normalization."""
        test_cases = [
            ("16 : 9", "16:9"),
            ("1920 X 1080", "1920x1080"),
            ("vid", "video"),
            ("aud", "audio"),
            ("sub", "subtitle"),
        ]

        for original, expected in test_cases:
            enhanced = self.enhancer.enhance_prompt(original, {})
            assert expected in enhanced

    def test_complex_prompt_enhancement(self):
        """Test enhancement of complex prompts."""
        original = "make vid vertical for IG with high quality and add subs"
        enhanced = self.enhancer.enhance_prompt(original, self.sample_context)

        # Should contain multiple enhancements
        assert "video" in enhanced  # vid -> video
        assert "9:16 aspect ratio" in enhanced  # vertical
        assert "IG" in enhanced  # IG stays as IG
        assert "high quality (lower CRF value)" in enhanced
        assert "add subs" in enhanced  # subs stays as subs
        assert "using video file" in enhanced  # context enhancement
        # Note: "subs" doesn't trigger subtitle context enhancement, only "subtitle" or "caption" does

    def test_empty_prompt(self):
        """Test handling of empty prompts."""
        enhanced = self.enhancer.enhance_prompt("", {})
        assert enhanced == ""

    def test_whitespace_handling(self):
        """Test proper whitespace handling."""
        original = "  convert   to   16:9  aspect  ratio  "
        enhanced = self.enhancer.enhance_prompt(original, {})
        assert "convert to 16:9 aspect ratio" in enhanced


class TestPromptSuggestions:
    """Test prompt improvement suggestions."""

    def test_vague_term_suggestions(self):
        """Test suggestions for vague terms."""
        suggestions = get_prompt_suggestions("make it better")
        assert any("Replace 'better'" in s for s in suggestions)

        suggestions = get_prompt_suggestions("good quality")
        assert any("Replace 'good'" in s for s in suggestions)

    def test_missing_file_specifications(self):
        """Test suggestions for missing file specifications."""
        suggestions = get_prompt_suggestions("convert file")
        assert any("Specify file format" in s for s in suggestions)

    def test_missing_quality_specifications(self):
        """Test suggestions for missing quality specifications."""
        suggestions = get_prompt_suggestions("high quality")
        assert any("Specify quality level" in s for s in suggestions)

    def test_missing_aspect_ratio(self):
        """Test suggestions for missing aspect ratio."""
        suggestions = get_prompt_suggestions("resize video")
        assert any("Specify target aspect ratio" in s for s in suggestions)

    def test_good_prompt_no_suggestions(self):
        """Test that good prompts don't generate suggestions."""
        suggestions = get_prompt_suggestions(
            "convert video.mp4 to 16:9 aspect ratio with small file size"
        )
        assert len(suggestions) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_enhance_user_prompt(self):
        """Test the enhance_user_prompt convenience function."""
        original = "make it vertical"
        context = {"videos": ["/path/to/video.mp4"]}

        enhanced = enhance_user_prompt(original, context)
        assert "9:16 aspect ratio" in enhanced
        assert "using video file" in enhanced

    def test_get_prompt_suggestions(self):
        """Test the get_prompt_suggestions convenience function."""
        suggestions = get_prompt_suggestions("make it better")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestIntegration:
    """Test integration with real-world scenarios."""

    def test_instagram_reel_scenario(self):
        """Test enhancement for Instagram Reel scenario."""
        original = "convert test.mp4 into vertical Instagram Reel (1080x1920), burn in captions from subs.srt with background box for readability, save as reel_captions.mp4"
        context = {
            "videos": ["/path/to/test.mp4"],
            "subtitle_files": ["/path/to/subs.srt"],
        }

        enhanced = enhance_user_prompt(original, context)

        # Should contain various enhancements
        assert "Instagram Reels (9:16 aspect ratio, 1080x1920)" in enhanced
        assert "burn in captions" in enhanced
        assert "using video file" in enhanced
        assert "using subtitle file" in enhanced

    def test_youtube_scenario(self):
        """Test enhancement for YouTube scenario."""
        original = "convert video for YouTube videos with high quality"
        context = {"videos": ["/path/to/video.mp4"]}

        enhanced = enhance_user_prompt(original, context)

        assert "YouTube videos (16:9 aspect ratio, 1920x1080)" in enhanced
        assert "high quality (lower CRF value)" in enhanced
        assert "using video file" in enhanced

    def test_compression_scenario(self):
        """Test enhancement for compression scenario."""
        original = "compress video for small file size"
        context = {"videos": ["/path/to/video.mp4"]}

        enhanced = enhance_user_prompt(original, context)

        assert "compress for smaller file size" in enhanced
        assert "small file size (higher CRF value)" in enhanced
        assert "using video file" in enhanced
