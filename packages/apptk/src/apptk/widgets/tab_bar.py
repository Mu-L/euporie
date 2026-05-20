"""Define widget for defining layouts."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, ClassVar, NamedTuple

from apptk.border import OutsetGrid
from apptk.cache import SimpleCache
from apptk.formatted_text.base import to_formatted_text
from apptk.formatted_text.utils import fragment_list_width, truncate
from apptk.layout.controls import (
    GetLinePrefixCallable,
    UIContent,
    UIControl,
)
from apptk.layout.utils import explode_text_fragments
from apptk.mouse_events import MouseButton, MouseEventType

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from apptk.border import GridStyle
    from apptk.formatted_text.base import (
        AnyFormattedText,
        OneStyleAndTextTuple,
        StyleAndTextTuples,
    )
    from apptk.key_binding.key_bindings import (
        NotImplementedOrNone,
    )
    from apptk.mouse_events import MouseEvent

log = logging.getLogger(__name__)


class TabBarTab(NamedTuple):
    """A class representing a tab and its callbacks."""

    title: AnyFormattedText
    on_activate: Callable[[], NotImplementedOrNone]
    on_deactivate: Callable[[], NotImplementedOrNone] | None = None
    on_close: Callable[[], NotImplementedOrNone] | None = None
    closeable: bool = False

    def __hash__(self) -> int:
        """Hash the Tab based on current title value."""
        return hash(tuple(to_formatted_text(self.title))) * hash(
            (self.on_activate, self.on_deactivate, self.on_close, self.closeable)
        )


class TabBarControl(UIControl):
    """A control which shows a tab bar."""

    char_scroll_left = "◀"
    char_scroll_right = "▶"
    char_close: ClassVar[str] = "✖"

    def __init__(
        self,
        tabs: Sequence[TabBarTab] | Callable[[], Sequence[TabBarTab]],
        active: int | Callable[[], int],
        spacing: int = 1,
        max_title_width: int = 30,
        grid: GridStyle = OutsetGrid,
    ) -> None:
        """Create a new tab bar instance.

        Args:
            tabs: A list to tuples describing the tab title and the callback to run
                when the tab is activated.
            active: The index of the currently active tab
            spacing: The number of characters between the tabs
            max_title_width: The maximum width of the title to display
            grid: The grid style to use for drawing borders

        """
        self._tabs = tabs
        self.spacing = spacing
        self.max_title_width = max_title_width
        self._active = active
        self._last_active: int | None = None
        self.scroll = -1
        self.grid = grid

        self.mouse_handlers: dict[int, Callable[[], NotImplementedOrNone] | None] = {}
        self.tab_widths: list[int] = []
        # Caches
        self.render_tab = lru_cache(self._render_tab)
        self._content_cache: SimpleCache = SimpleCache(maxsize=50)

    @property
    def tabs(self) -> list[TabBarTab]:
        """Return the tab-bar's tabs."""
        if callable(self._tabs):
            return list(self._tabs())
        else:
            return list(self._tabs)

    @tabs.setter
    def tabs(self, tabs: Sequence[TabBarTab]) -> None:
        """Set the tab bar's current tabs."""
        self._tabs = tabs

    @property
    def active(self) -> int:
        """Return the index of the active tab."""
        current_active = self._active() if callable(self._active) else self._active

        # Check if active tab has changed
        if self._last_active != current_active:
            # Handle tab switching
            if self._last_active is not None and 0 <= self._last_active < len(
                self.tabs
            ):
                old_tab = self.tabs[self._last_active]
                if callable(on_deactivate := old_tab.on_deactivate):
                    on_deactivate()

            # Call on_activate for new tab
            if current_active is not None and 0 <= current_active < len(self.tabs):
                new_tab = self.tabs[current_active]
                if callable(on_activate := new_tab.on_activate):
                    on_activate()

            # Ensure active tab is visible
            self.scroll_to(current_active)

            # Update last known active value
            self._last_active = current_active

        return current_active

    @active.setter
    def active(self, active: int | Callable[[], int]) -> None:
        """Set the currently active tab."""
        # Store new active value
        self._active = active

        # If it's a direct value (not callable), handle tab switching immediately
        if not callable(active):
            # Force property getter to handle the change
            _ = self.active

    def preferred_width(self, max_available_width: int) -> int | None:
        """Return the preferred width of the tab-bar control, the maximum available."""
        return max_available_width

    def preferred_height(
        self,
        width: int,
        max_available_height: int,
        wrap_lines: bool,
        get_line_prefix: GetLinePrefixCallable | None,
    ) -> int | None:
        """Return the preferred height of the tab-bar control (2 rows)."""
        return 2

    def is_focusable(self) -> bool:
        """Tell whether this user control is focusable."""
        return False

    def create_content(self, width: int, height: int) -> UIContent:
        """Generate the formatted text fragments which make the controls output."""
        self.available_width = width

        def get_content() -> tuple[
            UIContent, dict[int, Callable[[], NotImplementedOrNone] | None]
        ]:
            *fragment_lines, mouse_handlers = self.render(width)

            return UIContent(
                get_line=lambda i: fragment_lines[i],
                line_count=len(fragment_lines),
                show_cursor=False,
            ), mouse_handlers

        key = (hash(tuple(self.tabs)), width, self.active, self.scroll)
        ui_content, self.mouse_handlers = self._content_cache.get(key, get_content)
        return ui_content

    def scroll_to(self, active: int) -> None:
        """Adjust scroll position to ensure the active tab is visible."""
        # Calculate position of active tab
        pos = self.spacing  # Initial spacing
        for i in range(len(self.tabs)):
            if i == active:
                # Found active tab - check if it's visible
                tab_width = self.tab_widths[i] if i < len(self.tab_widths) else 0
                # Scroll left if tab start is before visible area
                if pos < self.scroll:
                    self.scroll = pos - self.spacing - 1
                # Scroll right if tab end is after visible area
                elif pos + tab_width > self.scroll + self.available_width:
                    self.scroll = pos + tab_width - self.available_width + 2
                break

            # Add tab width and spacing
            pos += (
                self.tab_widths[i] if i < len(self.tab_widths) else 0
            ) + self.spacing

    def _render_tab(
        self,
        title: tuple[OneStyleAndTextTuple, ...],
        on_activate: Callable[[], NotImplementedOrNone],
        on_deactivate: Callable[[], NotImplementedOrNone] | None,
        on_close: Callable[[], NotImplementedOrNone] | None,
        closeable: bool,
        active: bool,
        max_title_width: int,
        grid: GridStyle,
    ) -> tuple[
        StyleAndTextTuples,
        StyleAndTextTuples,
        list[Callable[[], NotImplementedOrNone] | None],
    ]:
        """Render the tab as formatted text.

        Args:
            title: The formatted text fragments making up the tab's title
            on_activate: Callback function to run when the tab is activated
            on_deactivate: Optional callback function to run when the tab is deactivated
            on_close: Optional callback function to run when the tab is closed
            closeable: Whether the tab can be closed
            active: Whether this tab is currently active
            max_title_width: Maximum width to display the tab title
            grid: The grid style to use for drawing borders

        Returns:
            Tuple containing:
            - Top line formatted text fragments
            - Bottom line formatted text fragments
            - List of mouse handler callbacks for each character position
        """
        title_ft = truncate(list(title), max_title_width)
        title_width = fragment_list_width(title_ft)
        style = "class:active" if active else "class:inactive"

        top_line: StyleAndTextTuples = explode_text_fragments([])
        tab_line: StyleAndTextTuples = explode_text_fragments([])
        mouse_handlers: list[Callable[[], NotImplementedOrNone] | None] = []

        # Add top edge over title
        top_line.append(
            (f"{style} class:tab,border,top", grid.TOP_MID * (title_width + 2))
        )

        # Left edge
        tab_line.append((f"{style} class:tab,border,left", grid.MID_LEFT))
        mouse_handlers.append(on_activate)

        # Title
        tab_line.extend(
            [
                (f"{style} class:tab,title {frag_style}", text)
                for frag_style, text, *_ in title_ft
            ]
        )
        for _ in range(title_width):
            mouse_handlers.append(on_activate)

        # Close button
        if closeable:
            top_line.append((f"{style} class:tab,border,top", grid.TOP_MID * 2))
            mouse_handlers.append(on_activate)
            tab_line.extend(
                [
                    (f"{style} class:tab", " "),
                    (f"{style} class:tab,close", self.char_close),
                ]
            )
            mouse_handlers.append(on_close)

        # Right edge
        tab_line.append((f"{style} class:tab,border,right", grid.MID_RIGHT))
        mouse_handlers.append(on_activate)

        return (top_line, tab_line, mouse_handlers)

    def render(
        self, width: int
    ) -> tuple[
        StyleAndTextTuples,
        StyleAndTextTuples,
        dict[int, Callable[[], NotImplementedOrNone] | None],
    ]:
        """Render the tab-bar as lines of formatted text."""
        top_line: StyleAndTextTuples = []
        tab_line: StyleAndTextTuples = []
        mouse_handlers: dict[int, Callable[[], NotImplementedOrNone] | None] = {}
        pos = 0
        full = 0

        renderings = [
            self.render_tab(
                title=tuple(to_formatted_text(tab.title)),
                max_title_width=self.max_title_width,
                on_activate=tab.on_activate,
                on_deactivate=tab.on_deactivate,
                on_close=tab.on_close,
                closeable=tab.closeable,
                active=(self.active == j),
                grid=self.grid,
            )
            for j, tab in enumerate(self.tabs)
        ]
        self.tab_widths = [len(x[0]) for x in renderings]

        # Do initial scroll if first render
        if self.scroll == -1:
            self.scroll_to(self._active() if callable(self._active) else self._active)

        # Apply scroll limits
        self.scroll = max(
            0,
            min(
                self.scroll,
                self.spacing * (len(self.tabs) + 1)
                + sum(len(x[1]) for x in renderings)
                - width,
            ),
        )
        scroll = self.scroll

        # Initial spacing
        for _ in range(self.spacing):
            if full >= scroll:
                top_line += [("", " ")]
                tab_line += [("class:border,bottom", self.grid.TOP_MID)]
                pos += 1
            full += 1

        for rendering in renderings:
            # Add the rendered tab content
            for tab_top, tab_bottom, handler in zip(*rendering):
                if full >= scroll:
                    top_line.append(tab_top)
                    tab_line.append(tab_bottom)
                    mouse_handlers[pos] = handler
                    pos += 1
                full += 1
                if pos == width:
                    break

            if pos == width:
                break

            # Inter-tab spacing
            if rendering is not renderings[-1]:
                if full >= scroll:
                    for _ in range(self.spacing):
                        top_line += [("", " ")]
                        tab_line += [("class:border,bottom", self.grid.TOP_MID)]
                        if pos == width:
                            break
                        pos += 1
                full += 1

            if pos == width:
                break

        # Add scroll indicators
        if scroll > 0:
            top_line[0] = ("", " ")
            tab_line[0] = ("class:overflow", self.char_scroll_left)
        if pos >= width:
            top_line[-1] = ("", " ")
            tab_line[-1] = ("class:overflow", self.char_scroll_right)
        else:
            # Otherwise add border to fill width
            tab_line += [
                (
                    "class:border,bottom",
                    self.grid.TOP_MID * (width - pos + 1),
                )
            ]

        return top_line, tab_line, mouse_handlers

    def mouse_handler(self, mouse_event: MouseEvent) -> NotImplementedOrNone:
        """Handle mouse events."""
        row = mouse_event.position.y
        col = mouse_event.position.x

        if row == 1 and mouse_event.event_type == MouseEventType.MOUSE_UP:
            if mouse_event.button == MouseButton.LEFT and callable(
                handler := self.mouse_handlers.get(col)
            ):
                # Activate the tab
                handler()
                return None
            elif mouse_event.button == MouseButton.MIDDLE:
                if callable(handler := self.mouse_handlers.get(col)):
                    # Activate tab
                    handler()
                    # Close the now active tab
                    tabs = self.tabs
                    tab = tabs[self.active]
                    if tab.closeable and callable(tab.on_close):
                        tab.on_close()
                return None

        tabs = self.tabs
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            index = max(self.active - 1, 0)
            if index != self.active:
                if callable(activate := tabs[index].on_activate):
                    activate()
                return None
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            index = min(self.active + 1, len(tabs) - 1)
            if index != self.active:
                if callable(activate := tabs[index].on_activate):
                    activate()
                return None
        return NotImplemented
