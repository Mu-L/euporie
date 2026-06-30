"""This package defines the euporie application and its components."""

from typing import Any


def __getattr__(name: str) -> Any:
    """Lazily load the package version from metadata on first access."""
    if name == "__version__":
        from importlib.metadata import version

        return version("euporie-core")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__app_name__ = "euporie"
__logo__ = "⚈"
__strapline__ = "Jupyter in the terminal"
__author__ = "Josiah Outram Halstead"
__email__ = "josiah@halstead.email"
__copyright__ = f"© 2025, {__author__}"
__license__ = "MIT"
