"""A multi-user hub euporie application."""

from typing import Any


def __getattr__(name: str) -> Any:
    """Lazily load the package version from metadata on first access."""
    if name == "__version__":
        from importlib.metadata import version

        return version("euporie-hub")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
