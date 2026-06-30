"""Euporie - A suite of terminal applications for interacting with Jupyter kernels."""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    """Lazily load the package version from metadata on first access."""
    if name == "__version__":
        from importlib.metadata import version

        return version("euporie")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
