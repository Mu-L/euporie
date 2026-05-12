"""Define custom inputs and outputs, and related methods."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import IO, Any, TextIO


log = logging.getLogger(__name__)


@lru_cache
def _have_termios_tty_fcntl() -> bool:
    try:
        import fcntl  # noqa F401
        import termios  # noqa F401
        import tty  # noqa F401
    except ModuleNotFoundError:
        return False
    else:
        return True


def _tiocgwinsz() -> tuple[int, int, int, int]:
    """Get the size and pixel dimensions of the terminal with `termios`."""
    import array

    output = array.array("H", [0, 0, 0, 0])
    if _have_termios_tty_fcntl():
        import fcntl
        import termios

        try:
            fcntl.ioctl(1, termios.TIOCGWINSZ, output)
        except OSError:
            pass
    rows, cols, xpixels, ypixels = output
    return rows, cols, xpixels, ypixels


class PseudoTTY:
    """Make an output stream look like a TTY."""

    fake_tty = True

    def __init__(self, underlying: IO[str] | TextIO, isatty: bool = True) -> None:
        """Wrap an underlying output stream.

        Args:
            underlying: The underlying output stream
            isatty: The value to return from :py:method:`PseudoTTY.isatty`.

        """
        self._underlying = underlying
        self._isatty = isatty

    def isatty(self) -> bool:
        """Determine if the stream is interpreted as a TTY."""
        return self._isatty

    def __getattr__(self, name: str) -> Any:
        """Return an attribute of the wrappeed stream."""
        return getattr(self._underlying, name)
