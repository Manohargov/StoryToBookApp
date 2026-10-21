"""Exception hierarchy shared across the application."""

from __future__ import annotations


class StoryToBookError(Exception):
    """Base class for every error raised by StoryToBook."""


class ProviderUnavailableError(StoryToBookError):
    """A provider was requested but its dependencies or credentials are missing."""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.hint = hint


class ProviderError(StoryToBookError):
    """A provider was available but failed while doing its job."""


class ProjectNotFoundError(StoryToBookError):
    """Raised when a project id does not exist in the library."""


class ExportError(StoryToBookError):
    """Raised when a book could not be rendered to the requested format."""
