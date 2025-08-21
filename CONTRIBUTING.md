# Contributing to ai-ffmpeg-cli

Thank you for your interest in contributing to ai-ffmpeg-cli! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

We welcome contributions from the community! Here are the main ways you can help:

### 🐛 Bug Reports

Found a bug? Please report it! Before creating an issue:

1. **Check existing issues** - Search for similar problems
2. **Provide details** - Include error messages, steps to reproduce, and system info
3. **Test with latest version** - Ensure you're using the most recent release

**Bug report template:**
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Run command: `aiclip "your command here"`
2. Expected: [what should happen]
3. Actual: [what actually happened]

## Environment
- OS: [macOS/Windows/Linux]
- Python version: [3.10+]
- ai-ffmpeg-cli version: [version]
- ffmpeg version: [version]

## Error Messages
```
[Paste any error messages here]
```

## Additional Context
Any other relevant information
```

### 💡 Feature Requests

Have an idea for a new feature? We'd love to hear it!

**Feature request template:**
```markdown
## Feature Description
Brief description of the feature

## Use Case
How would this feature be used? What problem does it solve?

## Proposed Implementation
Any thoughts on how this could be implemented?

## Alternatives Considered
Are there other ways to solve this problem?
```

### 📝 Documentation

Help improve our documentation! Areas that need attention:

- **README.md** - Main project documentation
- **Code comments** - Inline documentation
- **Examples** - Usage examples and tutorials
- **Troubleshooting** - Common issues and solutions

### 🧪 Testing

Help us maintain code quality by:

- **Writing tests** - Add tests for new features
- **Running tests** - Ensure existing tests pass
- **Test coverage** - Improve test coverage

### 🔧 Code Contributions

Ready to write code? Here's how to get started:

## 🛠️ Development Setup

### Prerequisites

- **Python 3.10+**
- **ffmpeg** installed and in PATH
- **Git** for version control
- **OpenAI API key** for testing

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/d-k-patel/ai-ffmpeg-cli.git
   cd ai-ffmpeg-cli
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables**
   ```bash
   cp .env.sample .env
   # Edit .env with your OpenAI API key
   ```

5. **Run tests**
   ```bash
   pytest
   ```

### Project Structure

```
ai-ffmpeg-cli/
├── src/ai_ffmpeg_cli/          # Main source code
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration management
│   ├── llm_client.py           # AI model integration
│   ├── intent_router.py        # Command routing
│   ├── executor.py             # Command execution
│   ├── prompt_enhancer.py      # Prompt optimization
│   ├── context_scanner.py      # File context scanning
│   └── path_security.py        # Security validation
├── tests/                      # Test suite
├── docs/                       # Documentation
├── assets/                     # Images and resources
└── README.md                   # Project documentation
```

## 📋 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 88 characters (Black formatter)
- **Type hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Imports**: Organized with `isort`

### Code Quality Tools

We use several tools to maintain code quality:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
mypy src/

# Run all quality checks
make lint
```

### Testing Guidelines

- **Test coverage**: Aim for >90% coverage
- **Test types**: Unit tests, integration tests, and CLI tests
- **Test naming**: Descriptive test names that explain the scenario
- **Fixtures**: Use pytest fixtures for common setup

**Example test structure:**
```python
def test_feature_name_success_case():
    """Test that feature works correctly in normal case."""
    # Arrange
    input_data = "test input"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   make lint
   make test
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(cli): add --output-dir option for custom output directory
fix(llm): resolve duration parameter not being applied to GIFs
docs(readme): update installation instructions
test(executor): add tests for command validation
```

### Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why (not how)
3. **Related issues**: Link to any related issues
4. **Screenshots**: Include screenshots for UI changes
5. **Testing**: Describe how to test your changes

**PR template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test addition/update
- [ ] Other (please describe)

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or breaking changes documented)
```

## 🎯 Areas for Contribution

### High Priority

- **Duration handling improvements** - Better support for time-based requests
- **Error handling** - More user-friendly error messages
- **Performance optimization** - Faster command generation
- **Test coverage** - Improve test coverage for edge cases

### Medium Priority

- **New ffmpeg operations** - Support for more complex operations
- **UI improvements** - Better interactive mode experience
- **Documentation** - More examples and tutorials
- **Integration tests** - End-to-end testing

### Low Priority

- **Performance monitoring** - Metrics and analytics
- **Plugin system** - Extensibility framework
- **GUI mode** - Visual interface
- **Batch processing** - Multi-file operations

## 🐛 Common Issues

### Development Environment

**"Module not found" errors**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

**"ffmpeg not found"**
```bash
# Install ffmpeg
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu
# Windows: download from ffmpeg.org
```

**"OpenAI API key required"**
```bash
# Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Testing Issues

**"Tests failing"**
```bash
# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=src/ai_ffmpeg_cli
```

## Getting Help

### Community Support

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion

### Development Questions

- **Code reviews**: Ask questions in PR comments
- **Architecture decisions**: Open a discussion
- **Implementation help**: Create an issue with "help wanted" label

## 🏆 Recognition

We appreciate all contributions! Contributors will be:

- **Listed in contributors** - Added to the project contributors list
- **Mentioned in releases** - Credit in release notes
- **Invited to discussions** - Participate in project decisions

## 📄 License

By contributing to ai-ffmpeg-cli, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ai-ffmpeg-cli! 🎬

Your contributions help make video processing easier for everyone.

