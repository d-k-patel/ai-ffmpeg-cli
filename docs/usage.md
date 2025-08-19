# Usage

```bash
aiclip "convert input.mov to mp4 with h264 and aac"
aiclip "trim first 30 seconds from video.mp4"
aiclip --dry-run "compress large-video.mp4"
```

Options:
- `--yes`: skip confirmation
- `--dry-run`: preview only
- `--model gpt-4o-mini`: pick model

## Subcommand mode

Global options must come before the subcommand. The primary subcommand is `nl` (natural language):

```bash
# Run with confirmation skipped
aiclip --yes nl "thumbnail at 10s from test.mp4"

# Preview only and override model
aiclip --dry-run --model gpt-4o-mini nl "compress input.mp4"
```

Avoid invoking the binary twice:

```bash
# Incorrect
aiclip aiclip --yes nl "..."
```
