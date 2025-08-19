from pathlib import Path

from ai_ffmpeg_cli.command_builder import build_commands
from ai_ffmpeg_cli.nl_schema import CommandEntry
from ai_ffmpeg_cli.nl_schema import CommandPlan


def test_convert_defaults_to_h264_aac():
    plan = CommandPlan(
        summary="Convert 1 file(s) to mp4 h264+aac with optional scale -",
        entries=[
            CommandEntry(input=Path("input.mov"), output=Path("input.mp4"), args=[]),
        ],
    )
    cmds = build_commands(plan, assume_yes=False)
    assert cmds == [
        ["ffmpeg", "-i", "input.mov", "-c:v", "libx264", "-c:a", "aac", "input.mp4"]
    ]


def test_extract_audio_command():
    plan = CommandPlan(
        summary="Extract audio from 1 file(s) to mp3",
        entries=[
            CommandEntry(
                input=Path("demo.mp4"),
                output=Path("demo.mp3"),
                args=["-q:a", "0", "-map", "a"],
            ),
        ],
    )
    cmds = build_commands(plan)
    assert cmds == [["ffmpeg", "-i", "demo.mp4", "-q:a", "0", "-map", "a", "demo.mp3"]]


def test_trim_copy_streams():
    plan = CommandPlan(
        summary="Trim 1 file(s) start=00:00:00 duration=30",
        entries=[
            CommandEntry(
                input=Path("input.mp4"),
                output=Path("clip.mp4"),
                args=["-ss", "00:00:00", "-t", "30"],
            ),
        ],
    )
    cmds = build_commands(plan)
    assert cmds == [
        [
            "ffmpeg",
            "-ss",
            "00:00:00",
            "-t",
            "30",
            "-i",
            "input.mp4",
            "-c",
            "copy",
            "clip.mp4",
        ]
    ]


def test_thumbnail_at_10s():
    plan = CommandPlan(
        summary="Thumbnail from 1 file(s) at 00:00:10",
        entries=[
            CommandEntry(
                input=Path("input.mp4"),
                output=Path("thumbnail.png"),
                args=["-ss", "00:00:10", "-vframes", "1"],
            ),
        ],
    )
    cmds = build_commands(plan)
    assert cmds == [
        [
            "ffmpeg",
            "-ss",
            "00:00:10",
            "-i",
            "input.mp4",
            "-vframes",
            "1",
            "thumbnail.png",
        ]
    ]


def test_overlay_top_right_default_with_logo_input():
    plan = CommandPlan(
        summary="Overlay logo.png on 1 file(s)",
        entries=[
            CommandEntry(
                input=Path("video.mp4"),
                output=Path("video_overlay.mp4"),
                args=[],
                extra_inputs=[Path("logo.png")],
            ),
        ],
    )
    cmds = build_commands(plan)
    assert cmds == [
        [
            "ffmpeg",
            "-i",
            "video.mp4",
            "-i",
            "logo.png",
            "-filter_complex",
            "overlay=W-w-10:10",
            "video_overlay.mp4",
        ]
    ]


def test_overlay_custom_xy_skips_default():
    plan = CommandPlan(
        summary="Overlay logo.png on 1 file(s)",
        entries=[
            CommandEntry(
                input=Path("video.mp4"),
                output=Path("video_overlay.mp4"),
                args=["-filter_complex", "overlay=5:10"],
                extra_inputs=[Path("logo.png")],
            ),
        ],
    )
    cmds = build_commands(plan)
    assert cmds == [
        [
            "ffmpeg",
            "-i",
            "video.mp4",
            "-i",
            "logo.png",
            "-filter_complex",
            "overlay=5:10",
            "video_overlay.mp4",
        ]
    ]


def test_compress_default_and_override_crf():
    # default
    plan_default = CommandPlan(
        summary="Compress 1 file(s) with libx265 CRF 28",
        entries=[
            CommandEntry(
                input=Path("in.mp4"),
                output=Path("out.mp4"),
                args=[],
            )
        ],
    )
    cmds_default = build_commands(plan_default)
    assert cmds_default == [
        ["ffmpeg", "-i", "in.mp4", "-c:v", "libx265", "-crf", "28", "out.mp4"]
    ]

    # override via args (simulating router adding -crf 22)
    plan_override = CommandPlan(
        summary="Compress 1 file(s) with libx265 CRF 28",
        entries=[
            CommandEntry(
                input=Path("in.mp4"),
                output=Path("out.mp4"),
                args=["-crf", "22"],
            )
        ],
    )
    cmds_override = build_commands(plan_override)
    assert cmds_override == [
        [
            "ffmpeg",
            "-i",
            "in.mp4",
            "-c:v",
            "libx265",
            "-crf",
            "22",
            "out.mp4",
        ]
    ]


def test_frames_default_and_custom_fps():
    # default when not present
    plan_default = CommandPlan(
        summary="Extract frames from 1 file(s) with fps 1/5",
        entries=[
            CommandEntry(
                input=Path("in.mp4"),
                output=Path("in_frame_%04d.png"),
                args=[],
            )
        ],
    )
    cmds_default = build_commands(plan_default)
    assert cmds_default == [
        ["ffmpeg", "-i", "in.mp4", "-vf", "fps=1/5", "in_frame_%04d.png"]
    ]

    # custom fps present in args
    plan_custom = CommandPlan(
        summary="Extract frames from 1 file(s) with fps 2",
        entries=[
            CommandEntry(
                input=Path("in.mp4"),
                output=Path("in_frame_%04d.png"),
                args=["-vf", "fps=2"],
            )
        ],
    )
    cmds_custom = build_commands(plan_custom)
    assert cmds_custom == [
        ["ffmpeg", "-i", "in.mp4", "-vf", "fps=2", "in_frame_%04d.png"]
    ]
