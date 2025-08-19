from pathlib import Path

from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


def test_route_extract_audio_defaults_output_mp3():
    intent = FfmpegIntent(action=Action.extract_audio, inputs=[Path("demo.mp4")])
    plan = route_intent(intent)
    assert plan.entries[0].output.name == "demo.mp3"
    assert plan.entries[0].args == ["-q:a", "0", "-map", "a"]


def test_route_thumbnail_defaults():
    intent = FfmpegIntent(action=Action.thumbnail, inputs=[Path("input.mp4")], start="00:00:10")
    plan = route_intent(intent)
    assert plan.entries[0].output.name == "thumbnail.png"
    assert "-vframes" in plan.entries[0].args


def test_route_overlay_includes_extra_input():
    intent = FfmpegIntent(
        action=Action.overlay,
        inputs=[Path("video.mp4")],
        overlay_path=Path("logo.png"),
    )
    plan = route_intent(intent)
    entry = plan.entries[0]
    assert entry.extra_inputs and entry.extra_inputs[0].name == "logo.png"


def test_segment_start_end_routing():
    intent = FfmpegIntent(
        action=Action.segment,
        inputs=[Path("video.mp4")],
        start="00:00:05",
        end="00:00:10",
    )
    plan = route_intent(intent)
    args = plan.entries[0].args
    assert args == ["-ss", "00:00:05", "-to", "00:00:10"]


def test_segment_duration_routing():
    intent = FfmpegIntent(
        action=Action.segment,
        inputs=[Path("video.mp4")],
        start="00:00:05",
        duration=3.5,
    )
    plan = route_intent(intent)
    args = plan.entries[0].args
    assert args == ["-ss", "00:00:05", "-t", "3.5"]


def test_trim_with_start_and_end_prefers_to():
    intent = FfmpegIntent(
        action=Action.trim,
        inputs=[Path("video.mp4")],
        start="00:00:05",
        end="00:00:10",
    )
    plan = route_intent(intent)
    args = plan.entries[0].args
    assert args == ["-ss", "00:00:05", "-to", "00:00:10"]


def test_glob_expands_inputs(tmp_path):
    f1 = tmp_path / "a.mov"
    f2 = tmp_path / "b.mov"
    f1.write_bytes(b"1")
    f2.write_bytes(b"2")

    # Use a non-strict action that does not require inputs validation (e.g., frames)
    intent = FfmpegIntent(
        action=Action.frames,
        inputs=[],
        glob=str(tmp_path / "*.mov"),
        fps="1/5",
    )
    plan = route_intent(intent)
    assert len(plan.entries) == 2
    input_names = {e.input.name for e in plan.entries}
    assert input_names == {"a.mov", "b.mov"}
