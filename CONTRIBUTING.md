# Contributing to aiclip

Thank you for your interest in contributing to aiclip! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

We welcome contributions of all kinds:

- 🐛 **Bug reports** and feature requests
- 📖 **Documentation** improvements
- 🧪 **Test cases** for edge scenarios
- 💻 **Code contributions** for new features
- 🎨 **Examples** and tutorials
- 🔧 **Tooling** and development improvements

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- ffmpeg (for testing)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-ffmpeg-cli.git
   cd ai-ffmpeg-cli
   ```

2. **Set up the development environment**
   ```bash
   make setup
   source .venv/bin/activate
   ```

3. **Install the package in development mode**
   ```bash
   make install
   ```

4. **Run the test suite**
   ```bash
   make test
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test files
python -m pytest tests/test_main.py -v

# Run tests with specific markers
python -m pytest -m "not slow"  # Skip slow tests
python -m pytest -m integration # Run only integration tests
```

### Test Structure

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test complete workflows and real-world scenarios
- **Performance Tests**: Benchmark critical operations
- **Security Tests**: Validate input sanitization and security measures

### Writing Tests

- Follow the existing test patterns
- Use descriptive test names
- Mock external dependencies (API calls, file system)
- Test both success and failure scenarios
- Aim for high test coverage

## 🔧 Code Quality

### Pre-commit Checks

```bash
# Run all quality checks
make pre-commit

# Individual checks
make format    # Format code
make lint      # Check code quality
make test      # Run tests
```

### Code Style

We use several tools to maintain code quality:

- **Ruff**: Code formatting and linting
- **MyPy**: Type checking
- **Bandit**: Security analysis
- **Pytest**: Testing framework

### Type Hints

- Use type hints for all function parameters and return values
- Import types from `typing` module when needed
- Use `TYPE_CHECKING` for imports that are only needed for type checking

### Documentation

- Use docstrings for all public functions and classes
- Follow Google-style docstring format
- Include examples in docstrings where helpful
- Keep README and documentation up to date

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, etc.)
5. **Error messages** and stack traces
6. **Minimal example** that demonstrates the issue

## 💡 Feature Requests

When suggesting features:

1. **Clear description** of the feature
2. **Use case** and motivation
3. **Proposed implementation** (if you have ideas)
4. **Examples** of how it would be used

## 🔄 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   make pre-commit
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### PR Guidelines

- **Title**: Clear, descriptive title
- **Description**: Detailed description of changes
- **Tests**: Ensure all tests pass
- **Coverage**: Maintain or improve test coverage
- **Documentation**: Update docs if needed

## 🏗️ Architecture Overview

### Project Structure

```
ai-ffmpeg-cli/
├── src/ai_ffmpeg_cli/          # Main source code
│   ├── main.py                 # CLI entry point (Typer)
│   ├── cli_operations.py       # CLI business logic
│   ├── llm_client.py          # OpenAI integration
│   ├── command_builder.py     # ffmpeg command generation
│   ├── intent_router.py       # Intent routing logic
│   ├── executor.py            # Command execution
│   ├── config.py              # Configuration management
│   ├── security.py            # Security and validation
│   └── ...
├── tests/                     # Test suite
├── docs/                      # Documentation
└── ...
```

### Key Components

- **CLI Layer**: Typer-based command-line interface
- **Business Logic**: Core functionality in `cli_operations.py`
- **AI Integration**: OpenAI API for natural language processing
- **Command Building**: ffmpeg command generation
- **Execution**: Safe command execution with preview
- **Configuration**: Environment-based configuration
- **Security**: Input validation and sanitization

## 🚀 Development Workflow

### Daily Development

```bash
# Start development session
source .venv/bin/activate

# Make changes and test
make test

# Check code quality
make lint

# Format code
make format

# Run full pipeline
make all
```

### Adding New Features

1. **Plan the feature**
   - Define requirements
   - Consider edge cases
   - Plan testing strategy

2. **Implement incrementally**
   - Start with tests
   - Implement core functionality
   - Add error handling
   - Update documentation

3. **Test thoroughly**
   - Unit tests for new functions
   - Integration tests for workflows
   - Performance tests if needed

### Debugging

```bash
# Run with verbose logging
aiclip --verbose "your command"

# Run specific tests with debug output
python -m pytest tests/test_specific.py -v -s

# Check type issues
mypy src/ai_ffmpeg_cli/your_module.py
```

## 📚 Documentation

### Building Documentation

```bash
# Generate and serve documentation
make docs
```

### Documentation Structure

- **README.md**: Project overview and quick start
- **docs/**: Detailed documentation
- **CHANGELOG.md**: Version history
- **CONTRIBUTING.md**: This file

## 🔒 Security

### Security Guidelines

- Never commit API keys or sensitive data
- Validate and sanitize all inputs
- Use parameterized commands to prevent injection
- Follow security best practices for CLI tools

### Reporting Security Issues

If you find a security vulnerability, please:

1. **Do not** create a public issue
2. **Email** the maintainers directly
3. **Include** detailed information about the vulnerability
4. **Wait** for acknowledgment before public disclosure

## 🎯 Areas for Contribution

### High Priority

- **Performance improvements** for large files
- **Additional ffmpeg operations** support
- **Better error messages** and user experience
- **Integration tests** for edge cases

### Medium Priority

- **Documentation improvements**
- **Example scripts** and tutorials
- **CI/CD enhancements**
- **Development tooling**

### Low Priority

- **GUI interface** (future consideration)
- **Plugin system** for custom operations
- **Analytics and metrics**

## 🤝 Community

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the docs first

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

## 📝 License

By contributing to aiclip, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

Thank you to all contributors who have helped make aiclip better! Your contributions are greatly appreciated.

---

**Happy coding! 🎬**
