"""Define a Panel class for use in tab bars and docking splits."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apptk.filters import to_filter
from apptk.utils import Event

if TYPE_CHECKING:
    from collections.abc import Callable

    from apptk.filters import FilterOrBool
    from apptk.formatted_text.base import AnyFormattedText
    from apptk.layout.containers import AnyContainer


class Panel:
    """A panel that can be displayed in a tab bar or docking split.

    Args:
        title: The display title for this panel.
        content: Optional container content to display.
        closeable: Whether the panel can be closed (filter or bool).
        on_activate: Optional handler called when the panel is activated.
        on_deactivate: Optional handler called when the panel is deactivated.
        on_close: Optional handler called when the panel's close is requested.
    """

    def __init__(
        self,
        title: AnyFormattedText = "",
        content: AnyContainer | None = None,
        closeable: FilterOrBool = False,
        on_activate: Callable[[Panel], None] | None = None,
        on_deactivate: Callable[[Panel], None] | None = None,
        on_close: Callable[[Panel], None] | None = None,
    ) -> None:
        """Initialize the panel."""
        self.title = title
        self.content = content
        self.closeable = to_filter(closeable)

        self.on_activate: Event[Panel] = Event(self)
        self.on_deactivate: Event[Panel] = Event(self)
        self.on_close: Event[Panel] = Event(self)

        if on_activate is not None:
            self.on_activate += on_activate
        if on_deactivate is not None:
            self.on_deactivate += on_deactivate
        if on_close is not None:
            self.on_close += on_close
