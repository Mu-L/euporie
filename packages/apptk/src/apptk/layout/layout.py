"""Wrapper for the layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.layout.layout import Layout as PtkLayout
from prompt_toolkit.utils import Event

if TYPE_CHECKING:
    from prompt_toolkit.layout.containers import Window


__all__ = [
    "Layout",
]


class Layout(PtkLayout):
    """Extended layout that fires an event when focus changes.

    This subclass adds an :attr:`on_focus_changed` event that is triggered
    whenever the focused window changes.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize the layout."""
        self.on_focus_changed = Event(self)
        super().__init__(*args, **kwargs)

    @property
    def current_window(self) -> Window:
        """Return the :class:`.Window` object that is currently focused."""
        return self._stack[-1]

    @current_window.setter
    def current_window(self, value: Window) -> None:
        """Set the :class:`.Window` object to be currently focused."""
        previous = self._stack[-1] if self._stack else None
        self._stack.append(value)
        if value != previous:
            self.on_focus_changed.fire()
