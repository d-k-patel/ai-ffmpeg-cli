# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-19

### 🚀 Major Improvements

#### Architecture & Code Quality
- **Extracted CLI Logic**: Moved CLI operations from `main.py` to dedicated `cli_operations.py` module
- **Improved Testability**: CLI logic is now in pure functions that can be unit tested independently
- **Better Separation of Concerns**: Clear boundaries between CLI framework and business logic
- **Enhanced Error Handling**: Consistent error propagation and better exception handling

#### Testing & Quality Assurance
- **Comprehensive Test Coverage**: Increased from 80.32% to **87.67%** overall coverage
- **New Test Suite**: Added 19 new tests for `cli_operations.py` module
- **Enhanced Main Tests**: Added 15 new tests for `main.py` explain-cmd functionality
- **Integration Tests**: Improved error handling tests for various failure scenarios
- **Type Safety**: Fixed all mypy type checking issues with proper type annotations

#### Code Quality
- **Linting**: Fixed all ruff linting issues including unused variables
- **Formatting**: Consistent code formatting across the entire codebase
- **Type Safety**: Proper type hints and annotations throughout
- **Security**: Zero security vulnerabilities detected by Bandit

### 🔧 Technical Improvements

#### CLI Operations Module (`cli_operations.py`)
- `process_natural_language_prompt()` - Handles one-shot NL processing
- `process_interactive_session()` - Handles interactive mode with proper error recovery
- `_make_llm_client()` - Creates LLM client with secure API key handling
- `_execute_commands()` - Handles command execution with preview/confirmation
- `setup_logging()` - Centralized logging setup

#### Main Module Refactoring
- Simplified `main.py` to focus on Typer integration
- Removed duplicate preview logic
- Better error handling for different failure modes
- Cleaner command structure and parameter handling

#### Testing Infrastructure
- **Unit Tests**: Comprehensive testing of all CLI operations
- **Integration Tests**: Real-world scenario testing
- **Error Path Testing**: Coverage for all failure modes
- **Performance Tests**: Benchmarking for critical operations
- **Security Tests**: Input validation and sanitization testing

### 🐛 Bug Fixes

- **Duplicate Preview**: Fixed duplicate preview calls in one-shot and interactive modes
- **Command Building**: Simplified and made command building logic more deterministic
- **Authentication Errors**: Proper handling of API key validation and authentication failures
- **Type Annotations**: Fixed incorrect type imports and annotations
- **Unused Variables**: Removed unused variables in test files

### 📚 Documentation

- **Updated README**: Reflects current project status and improvements
- **Development Guide**: Enhanced development setup instructions
- **Configuration**: Added new environment variables and their descriptions
- **Troubleshooting**: Improved troubleshooting section with common issues

### 🛠️ Development Experience

- **Makefile**: Enhanced with new commands for development workflow
- **Pre-commit**: Added pre-commit hooks for code quality
- **CI/CD**: Improved GitHub Actions workflows
- **Dependencies**: Updated and organized development dependencies

### 🔒 Security & Safety

- **Input Sanitization**: Enhanced input validation to prevent command injection
- **Path Validation**: Improved path handling and validation
- **API Key Security**: Better API key handling and masking
- **Error Recovery**: Graceful handling of network timeouts and API failures

### 📊 Performance

- **Command Building**: Optimized command building logic
- **Error Handling**: Reduced overhead in error scenarios
- **Memory Usage**: Improved memory management in interactive sessions
- **Test Performance**: Faster test execution with better organization

## [0.1.4] - 2025-08-19

### 🐛 Bug Fixes
- Fixed command building logic for compression operations
- Improved error handling for malformed natural language input
- Enhanced timeout handling for LLM requests

### 🔧 Improvements
- Better default codec selection for different operations
- Improved context scanning for input files
- Enhanced error messages for common failure scenarios

## [0.1.3] - 2025-08-19

### ✨ New Features
- Added `explain-cmd` subcommand for ffmpeg command explanation
- Enhanced interactive mode with better error recovery
- Added support for batch processing operations

### 🔧 Improvements
- Better handling of file overwrite scenarios
- Improved natural language parsing accuracy
- Enhanced documentation and examples

## [0.1.2] - 2025-08-19

### 🐛 Bug Fixes
- Fixed API key validation issues
- Resolved command execution errors in certain scenarios
- Improved error handling for network timeouts

### 🔧 Improvements
- Better default model selection
- Enhanced configuration loading
- Improved test coverage

## [0.1.1] - 2025-08-19

### 🐛 Bug Fixes
- Fixed installation issues on certain platforms
- Resolved dependency conflicts
- Improved error messages

### 🔧 Improvements
- Better documentation
- Enhanced CLI help text
- Improved development setup

## [0.1.0] - 2025-08-19

### 🎉 Initial Release
- AI-powered natural language to ffmpeg command translation
- Interactive and one-shot command modes
- Preview and confirmation system
- Support for common video and audio operations
- Comprehensive error handling and safety features

---

## Contributing

To contribute to this changelog, please follow the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format and add your changes under the appropriate section.

## Version History

- **0.2.0**: Major architecture improvements, comprehensive testing, enhanced code quality
- **0.1.4**: Bug fixes and command building improvements
- **0.1.3**: New features including explain-cmd and batch processing
- **0.1.2**: API key validation and network timeout fixes
- **0.1.1**: Installation and dependency fixes
- **0.1.0**: Initial release with core functionality
