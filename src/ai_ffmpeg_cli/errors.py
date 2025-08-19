class ConfigError(Exception):
    """Raised when configuration or environment validation fails."""


class ParseError(Exception):
    """Raised when the LLM fails to produce a valid intent."""


class BuildError(Exception):
    """Raised when an intent cannot be routed or converted into commands."""


class ExecError(Exception):
    """Raised when command execution fails."""
