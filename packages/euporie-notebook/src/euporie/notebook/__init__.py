"""Define euporie's application classes."""

from typing import Any


def __getattr__(name: str) -> Any:
    """Lazily load the package version from metadata on first access."""
    if name == "__version__":
        from importlib.metadata import version

        return version("euporie-notebook")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
