# 🎬 aiclip

[![PyPI version](https://badge.fury.io/py/ai-ffmpeg-cli.svg)](https://badge.fury.io/py/ai-ffmpeg-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Stop Googling ffmpeg commands. Just describe what you want.**

**aiclip** is an AI-powered CLI that translates natural language into safe, previewable `ffmpeg` commands. Built for developers, content creators, and anyone who works with media files but doesn't want to memorize complex syntax.

## ✨ Why aiclip?

- 🤖 **AI-Native**: Translate plain English to perfect ffmpeg commands
- 🔒 **Safety First**: Preview every command before execution  
- ⚡ **10x Faster**: Skip the documentation, Stack Overflow, and trial-and-error
- 🎯 **Battle-Tested**: Generates reliable, production-ready commands
- 🔄 **Smart Defaults**: Sensible codec and quality settings out of the box

```bash
# Instead of this...
ffmpeg -i input.mp4 -vf "scale=1280:720" -c:v libx264 -c:a aac -b:v 2000k output.mp4

# Just say this...
aiclip "convert input.mp4 to 720p with good quality"
```

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install ai-ffmpeg-cli

# Or with Homebrew (coming soon)
brew install aiclip
```

### Setup

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Or create a .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### First Command

```bash
# Interactive mode - just describe what you want
aiclip
> convert this video to 720p
┌───┬──────────────────────────────────────────────────────────┐
│ # │ Command                                                  │
├───┼──────────────────────────────────────────────────────────┤
│ 1 │ ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264... │
└───┴──────────────────────────────────────────────────────────┘
Run these commands? [Y/n] 
```

## 📖 Usage Examples

### Video Processing
```bash
# Convert formats
aiclip "convert input.mov to mp4 with h264 and aac"

# Resize videos  
aiclip "downscale video.mp4 to 720p"
aiclip "make input.mp4 1080p resolution"

# Compress files
aiclip "compress large-video.mp4 to smaller size"
aiclip "reduce file size with CRF 23"
```

### Audio Operations
```bash
# Extract audio
aiclip "extract audio from movie.mp4 to mp3"
aiclip "get audio track from video as wav"

# Remove audio
aiclip "remove audio from video.mp4"
```

### Trimming & Cutting
```bash
# Time-based cutting
aiclip "trim first 30 seconds from video.mp4"
aiclip "keep segment from 2:15 to 3:45 in input.mp4"
aiclip "cut out middle 5 minutes"
```

### Image Extraction  
```bash
# Thumbnails
aiclip "create thumbnail at 10 seconds from video.mp4"
aiclip "extract frame at 2:30 as PNG"

# Frame sequences
aiclip "extract one frame every 5 seconds"
aiclip "get all frames from video as images"
```

### Advanced Operations
```bash
# Overlays
aiclip "add watermark logo.png to top-right of video.mp4"  
aiclip "overlay text on video at position 10:10"

# Batch processing
aiclip "convert all .mov files to .mp4"
```

## 🎛️ Command Line Options

```bash
# One-shot mode (no interaction)
aiclip "your command here"

# Skip confirmation prompts  
aiclip --yes "convert video.mp4 to 720p"

# Preview only (don't execute)
aiclip --dry-run "compress input.mp4"

# Use different AI model
aiclip --model gpt-4o-mini "extract audio"

# Increase timeout for complex requests
aiclip --timeout 120 "complex processing task"

# Verbose logging for troubleshooting
aiclip --verbose "your command"
```

### Subcommands and option placement

You can also use the explicit `nl` subcommand. Put global options before the subcommand:

```bash
aiclip --yes nl "thumbnail at 10s from test.mp4"
aiclip --dry-run --model gpt-4o-mini nl "compress input.mp4"
```

Do not invoke the binary twice:

```bash
# Incorrect
aiclip aiclip --yes nl "..."
```

## 🔧 Configuration

aiclip uses environment variables and `.env` files for configuration:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Optional
AICLIP_MODEL=gpt-4o              # AI model to use
AICLIP_DRY_RUN=false            # Preview commands by default
```

## 🎯 Smart Defaults & Safety

- **Preview First**: Every command is shown before execution
- **Overwrite Protection**: Warns before overwriting existing files  
- **Sensible Codecs**: Automatically chooses h264+aac for MP4, libx265 for compression
- **Stream Copy**: Uses `-c copy` for trimming when possible (faster, lossless)
- **Context Aware**: Scans your directory to suggest input files and durations

## 📊 Supported Operations

| Operation | Examples | ffmpeg Equivalent |
|-----------|----------|-------------------|
| **Convert** | "convert to mp4", "make it h264" | `-c:v libx264 -c:a aac` |
| **Resize** | "720p", "1920x1080", "scale to 50%" | `-vf scale=1280:720` |  
| **Compress** | "make smaller", "CRF 28" | `-c:v libx265 -crf 28` |
| **Extract Audio** | "get audio as mp3" | `-q:a 0 -map a` |
| **Trim** | "first 30 seconds", "2:15 to 3:45" | `-ss 00:02:15 -to 00:03:45` |
| **Thumbnail** | "frame at 10s" | `-ss 00:00:10 -vframes 1` |
| **Overlay** | "watermark top-right" | `-filter_complex overlay=W-w-10:10` |
| **Batch** | "all *.mov files" | Shell loops with glob patterns |

## 🛠️ Development

```bash
# Clone and setup
git clone https://github.com/yourusername/ai-ffmpeg-cli.git
cd ai-ffmpeg-cli
make setup

# Run tests
make test

# Check code quality  
make lint

# Try demo commands
make demo
```

## 📋 Requirements

- **Python 3.10+** (uses modern type hints)
- **ffmpeg** installed and available in PATH
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/)
- **OpenAI API key** for natural language processing

## 🆘 Troubleshooting

### Common Issues

**"OPENAI_API_KEY is required"**
```bash
# Set your API key
export OPENAI_API_KEY="sk-your-key-here"
# Or add it to .env file
```

**"ffmpeg not found in PATH"**  
```bash
# Install ffmpeg
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu
# Windows: download from ffmpeg.org
```

**"Failed to parse natural language prompt"**
- Try being more specific in your request
- Use `--model gpt-4o` for better accuracy  
- Increase timeout with `--timeout 120`
- Check your internet connection

**"No input files found"**
- Ensure files exist in current directory
- Check file extensions match your request
- Use `ls` to verify available files

### Getting Help

- 📖 **Documentation**: Full guides at [docs link]
- 💬 **Discord**: Join our community for real-time help
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/ai-ffmpeg-cli/issues)
- 💡 **Discussions**: Feature requests and Q&A on [GitHub Discussions](https://github.com/yourusername/ai-ffmpeg-cli/discussions)

## 🤝 Contributing

We love contributions! Whether it's:

- 🐛 **Bug reports** and feature requests
- 📖 **Documentation** improvements  
- 🧪 **Test cases** for edge scenarios
- 💻 **Code contributions** for new features
- 🎨 **Examples** and tutorials

See our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📈 What's Next?

- 🔄 **Batch Templates**: Save and reuse complex workflows
- 🎛️ **GUI Mode**: Visual interface for non-CLI users  
- ⚡ **Local Models**: Run without internet using local AI
- 🏢 **Team Features**: Shared commands and analytics
- 🔌 **Integrations**: GitHub Actions, Docker, CI/CD pipelines

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⭐ Support

If aiclip saves you time, please:
- ⭐ **Star** this repository  
- 🐦 **Share** on social media
- 📝 **Write** a review or blog post
- 💬 **Tell** your developer friends

---

<p align="center">
  <strong>Made with ❤️ by developers who got tired of Googling ffmpeg commands</strong><br>
  <sub>🎬 Turn your words into perfect video commands</sub>
</p>