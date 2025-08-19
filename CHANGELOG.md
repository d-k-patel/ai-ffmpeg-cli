# Changelog

All notable changes to aiclip will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Upcoming features will be listed here

### Changed
- Upcoming changes will be listed here

### Fixed
- Upcoming fixes will be listed here

## [0.1.3] - 2025-08-19

### Fixed
- CLI crash on `--help` due to unsupported `Optional[typer.Context]` annotation. Refactored callback to require `Context` and added an internal wrapper for tests.

### Changed
- Documentation updates clarifying correct usage of global options and subcommands. Added examples for `nl` subcommand and a note to avoid invoking the binary twice.

## [0.1.4] - 2025-08-19

### Documentation
- Fix README first command section formatting (interactive vs one-shot examples) and minor spacing in table snippet.

## [0.1.0] - 2024-01-XX

### Added
- 🎬 Initial release of aiclip
- 🤖 AI-powered natural language to ffmpeg command translation
- 🔒 Safety-first approach with command preview before execution
- ⚡ Support for common video operations:
  - Video format conversion (mov, mp4, etc.)
  - Video scaling and resolution changes
  - Video compression with quality control
  - Audio extraction and removal
  - Video trimming and segmentation
  - Thumbnail and frame extraction
  - Video overlay and watermarking
  - Batch processing with glob patterns

### Features
- Interactive CLI mode for iterative workflows
- One-shot command execution for automation
- Smart defaults for codecs and quality settings
- Context scanning for automatic file detection
- Comprehensive error handling with helpful messages
- Overwrite protection for existing files
- Rich terminal output with formatted tables
- Configurable AI models (GPT-4o, GPT-4o-mini)
- Environment-based configuration
- Dry-run mode for command preview
- Verbose logging for debugging

### Technical
- Python 3.10+ support
- Built with Typer for CLI framework
- OpenAI GPT integration for natural language processing
- Pydantic for robust data validation
- Rich for beautiful terminal output
- Comprehensive test suite with pytest
- Code quality tools (ruff, mypy)
- Docker support
- GitHub Actions CI/CD pipeline

### Documentation
- Comprehensive README with examples
- API documentation
- Contributing guidelines
- Development setup instructions

---

## Release Notes Template

When preparing a new release, copy this template:

### [X.Y.Z] - YYYY-MM-DD

#### Added
- New features

#### Changed  
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Now removed features

#### Fixed
- Bug fixes

#### Security
- Vulnerability fixes
