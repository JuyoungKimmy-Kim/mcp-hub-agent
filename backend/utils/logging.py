"""
Logging utility module using structlog for structured logging.
"""
import logging
import sys
from typing import Optional, Dict, Any
import structlog
from structlog.types import FilteringBoundLogger


class LogManager:
    """
    Singleton LogManager class for managing structured logging across the application.

    Uses structlog to provide structured, context-aware logging with support for
    both JSON and console output formats.

    Example:
        >>> log_manager = LogManager.get_instance()
        >>> logger = log_manager.get_logger("my_module")
        >>> logger.info("User logged in", user_id="123", email="user@example.com")
    """

    _instance: Optional['LogManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure only one instance of LogManager exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'LogManager':
        """Get the singleton instance of LogManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the LogManager (only once due to singleton)."""
        if not LogManager._initialized:
            self._configure_logging()
            LogManager._initialized = True

    def _configure_logging(
        self,
        log_level: str = "INFO",
        log_format: str = "console",
    ) -> None:
        """
        Configure structlog with appropriate processors and settings.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Output format ('json' for production, 'console' for development)
        """
        # Set the log level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=numeric_level,
        )

        # Configure processors based on format
        if log_format.lower() == "json":
            processors = [
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ]
        else:
            # Console format with colors for development
            processors = [
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ]

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def configure(
        self,
        log_level: str = "INFO",
        log_format: str = "console",
    ) -> None:
        """
        Reconfigure logging settings.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Output format ('json' for production, 'console' for development)
        """
        self._configure_logging(log_level, log_format)

    def get_logger(self, name: str, **initial_context: Any) -> FilteringBoundLogger:
        """
        Get a logger instance with optional initial context.

        Args:
            name: Logger name (typically module name)
            **initial_context: Initial context to bind to the logger

        Returns:
            A bound logger instance with the specified context

        Example:
            >>> logger = log_manager.get_logger("api.chat", service="chat_service")
            >>> logger.info("Processing request", request_id="abc123")
        """
        logger = structlog.get_logger(name)
        if initial_context:
            logger = logger.bind(**initial_context)
        return logger

    @staticmethod
    def bind_context(**context: Any) -> None:
        """
        Bind context to all loggers in the current context.

        This is useful for adding request-specific context (like request_id)
        that will be included in all log messages within the same context.

        Args:
            **context: Context key-value pairs to bind

        Example:
            >>> LogManager.bind_context(request_id="req-123", user_id="user-456")
            >>> # All subsequent logs will include these fields
        """
        structlog.contextvars.bind_contextvars(**context)

    @staticmethod
    def clear_context(*keys: str) -> None:
        """
        Clear specific context keys or all context.

        Args:
            *keys: Context keys to clear. If none provided, clears all context.

        Example:
            >>> LogManager.clear_context("request_id")  # Clear specific key
            >>> LogManager.clear_context()  # Clear all context
        """
        if keys:
            structlog.contextvars.unbind_contextvars(*keys)
        else:
            structlog.contextvars.clear_contextvars()


# Convenience function to get logger instance
def get_logger(name: str, **context: Any) -> FilteringBoundLogger:
    """
    Convenience function to get a logger instance.

    Args:
        name: Logger name (typically module name or __name__)
        **context: Initial context to bind to the logger

    Returns:
        A bound logger instance

    Example:
        >>> from backend.utils.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return LogManager.get_instance().get_logger(name, **context)
