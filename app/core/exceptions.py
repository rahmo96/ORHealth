"""Application-specific exception classes."""


class AppError(Exception):
    """Base exception for the application."""


class ValidationAppError(AppError):
    """Raised when input validation fails."""


class DatabaseAppError(AppError):
    """Raised when a database operation fails."""
