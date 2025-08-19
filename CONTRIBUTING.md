# Contributing to aiclip

Thank you for your interest in contributing to aiclip! 🎉

We welcome contributions of all kinds:
- 🐛 Bug reports and fixes
- ✨ New features and enhancements  
- 📖 Documentation improvements
- 🧪 Tests and quality improvements
- 💡 Ideas and suggestions

## Quick Start

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/ai-ffmpeg-cli.git
   cd ai-ffmpeg-cli
   ```

2. **Setup Development Environment**
   ```bash
   make setup
   source .venv/bin/activate
   ```

3. **Run Tests**
   ```bash
   make test
   make lint
   ```

4. **Make Changes & Test**
   ```bash
   # Make your changes
   make test          # Ensure tests pass
   make format        # Format code
   make demo          # Test functionality
   ```

5. **Submit Pull Request**
   - Create a feature branch
   - Make your changes with tests
   - Update documentation if needed
   - Submit PR with clear description

## Development Workflow

### Testing
```bash
make test              # Run all tests
make test-cov          # Run with coverage
make demo             # Manual testing
```

### Code Quality
```bash
make lint             # Check code quality
make format           # Auto-format code
make security         # Security checks
```

### Before Submitting
```bash
make pre-commit       # Run all checks
```

## Contribution Guidelines

### Bug Reports
Please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, ffmpeg version)
- Example command that fails

### Feature Requests
- Describe the use case
- Explain why it would be valuable
- Provide example usage if possible

### Code Contributions
- Follow existing code style
- Add tests for new functionality
- Update documentation
- Keep commits focused and descriptive

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Run `make format` to auto-format your code.

## Questions?

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Use GitHub Issues for bugs
- 📧 **Email**: Contact maintainers directly for sensitive issues

Thank you for contributing! 🚀
