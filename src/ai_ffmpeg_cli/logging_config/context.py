"""Contextual logging support using contextvars."""

import contextvars
from typing import Any

# Context variables for logging
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
_tenant_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)
_custom_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "custom_context", default=None
)


class LogContext:
    """Context manager for binding logging context."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize context with key-value pairs.

        Args:
            **kwargs: Context variables to bind
        """
        self.context_data = kwargs
        self._tokens: dict[str, contextvars.Token] = {}

    def __enter__(self) -> "LogContext":
        """Bind context variables."""
        for key, value in self.context_data.items():
            if key == "request_id":
                self._tokens[key] = _request_id.set(value)
            elif key == "user_id":
                self._tokens[key] = _user_id.set(value)
            elif key == "tenant_id":
                self._tokens[key] = _tenant_id.set(value)
            else:
                # Store custom context
                current_context = _custom_context.get() or {}
                current_context = current_context.copy()
                current_context[key] = value
                self._tokens[f"custom_{key}"] = _custom_context.set(current_context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore context variables."""
        for key, token in self._tokens.items():
            if key.startswith("custom_"):
                _custom_context.reset(token)
            elif key == "request_id":
                _request_id.reset(token)
            elif key == "user_id":
                _user_id.reset(token)
            elif key == "tenant_id":
                _tenant_id.reset(token)


def bind_context(**kwargs: Any) -> LogContext:
    """Create a context manager for binding logging context.

    Args:
        **kwargs: Context variables to bind

    Returns:
        LogContext instance that can be used as a context manager

    Example:
        with bind_context(request_id="req-123", user_id="user-456"):
            logger.info("Processing request")
    """
    return LogContext(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    _request_id.set(None)
    _user_id.set(None)
    _tenant_id.set(None)
    _custom_context.set(None)


def get_context() -> dict[str, Any]:
    """Get current context data.

    Returns:
        Dictionary containing current context variables
    """
    context = {}

    # Add standard context variables if set
    request_id_val = _request_id.get()
    if request_id_val is not None:
        context["request_id"] = request_id_val

    user_id_val = _user_id.get()
    if user_id_val is not None:
        context["user_id"] = user_id_val

    tenant_id_val = _tenant_id.get()
    if tenant_id_val is not None:
        context["tenant_id"] = tenant_id_val

    # Add custom context
    custom_context = _custom_context.get()
    if custom_context:
        context.update(custom_context)

    return context


def request_id(value: str) -> LogContext:
    """Create a context manager that binds request_id.

    Args:
        value: Request ID value

    Returns:
        LogContext instance

    Example:
        with request_id("req-123"):
            logger.info("Processing request")
    """
    return LogContext(request_id=value)


def user_id(value: str) -> LogContext:
    """Create a context manager that binds user_id.

    Args:
        value: User ID value

    Returns:
        LogContext instance

    Example:
        with user_id("user-456"):
            logger.info("User action")
    """
    return LogContext(user_id=value)


def tenant_id(value: str) -> LogContext:
    """Create a context manager that binds tenant_id.

    Args:
        value: Tenant ID value

    Returns:
        LogContext instance

    Example:
        with tenant_id("tenant-789"):
            logger.info("Tenant operation")
    """
    return LogContext(tenant_id=value)
