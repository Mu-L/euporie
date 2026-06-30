"""Shim package extending apptk."""

from typing import Any

from modshim import shim


def __getattr__(name: str) -> Any:
    """Lazily load the package version from metadata on first access."""
    if name == "__version__":
        from importlib.metadata import version

        return version("apptk")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


shim("prompt_toolkit", extras=["ptterm"])
