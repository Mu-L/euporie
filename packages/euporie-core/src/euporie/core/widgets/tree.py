"""Define a tree-view widget."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from apptk.application.current import get_app
from apptk.data_structures import Point
from apptk.key_binding import KeyBindings
from apptk.layout.containers import ScrollOffsets, Window
from apptk.layout.controls import FormattedTextControl, UIContent
from apptk.mouse_events import MouseButton, MouseEvent, MouseEventType

if TYPE_CHECKING:
    from typing import Any

    from apptk.formatted_text import StyleAndTextTuples
    from apptk.key_binding.key_bindings import NotImplementedOrNone


class _TreeControl(FormattedTextControl):
    """A formatted text control that exposes a cursor position for scrolling."""

    def __init__(self, tree_view: JsonView, **kwargs: Any) -> None:
        """Initialize the tree control."""
        self._tree_view = tree_view
        super().__init__(**kwargs)

    def create_content(self, width: int, height: int) -> UIContent:
        """Create UIContent with a cursor position for scroll tracking."""
        content = super().create_content(width, height)
        cursor_row = min(self._tree_view._selected_line, content.line_count - 1)
        cursor_row = max(0, cursor_row)
        return UIContent(
            get_line=content.get_line,
            line_count=content.line_count,
            cursor_position=Point(x=0, y=cursor_row),
            show_cursor=False,
        )

    def move_cursor_down(self) -> None:
        """Move the cursor down one line."""
        self._tree_view._selected_line = min(
            self._tree_view._line_count - 1, self._tree_view._selected_line + 1
        )

    def move_cursor_up(self) -> None:
        """Move the cursor up one line."""
        self._tree_view._selected_line = max(0, self._tree_view._selected_line - 1)


class JsonView:
    """A JSON-view container."""

    def __init__(
        self, data: Any, title: str | None = None, expanded: bool = False
    ) -> None:
        """Create a new instance."""
        self.data = data
        self.title = "root" if title is None else title
        self.start_expanded = expanded
        self._toggled_paths: set[tuple[str, ...]] = set()
        self._selected_line: int = 0
        self._line_count: int = 1
        self._line_paths: list[tuple[str, ...]] = [()]

        kb = KeyBindings()

        @kb.add("up")
        def _move_up(event: Any) -> None:
            """Move selection up."""
            self._selected_line = max(0, self._selected_line - 1)

        @kb.add("down")
        def _move_down(event: Any) -> None:
            """Move selection down."""
            self._selected_line = min(self._line_count - 1, self._selected_line + 1)

        @kb.add("enter")
        @kb.add(" ")
        def _toggle_selected(event: Any) -> None:
            """Toggle expansion of the selected node."""
            if 0 <= self._selected_line < len(self._line_paths):
                path = self._line_paths[self._selected_line]
                if path in self._toggled_paths:
                    self._toggled_paths.remove(path)
                else:
                    self._toggled_paths.add(path)

        @kb.add("home")
        def _move_home(event: Any) -> None:
            """Move selection to the first line."""
            self._selected_line = 0

        @kb.add("end")
        def _move_end(event: Any) -> None:
            """Move selection to the last line."""
            self._selected_line = self._line_count - 1

        @kb.add("pageup")
        def _page_up(event: Any) -> None:
            """Move selection up by a page."""
            window = self.container
            if window.render_info:
                page_size = window.render_info.window_height
            else:
                page_size = 10
            self._selected_line = max(0, self._selected_line - page_size)

        @kb.add("pagedown")
        def _page_down(event: Any) -> None:
            """Move selection down by a page."""
            window = self.container
            if window.render_info:
                page_size = window.render_info.window_height
            else:
                page_size = 10
            self._selected_line = min(
                self._line_count - 1, self._selected_line + page_size
            )

        self._control = _TreeControl(
            tree_view=self,
            text=self._get_formatted_text,
            focusable=True,
            key_bindings=kb,
        )
        self.container = Window(
            self._control,
            style="class:tree",
            scroll_offsets=ScrollOffsets(top=2, bottom=2),
        )

    def _get_value_style(self, value: Any) -> str:
        """Return the style for a given value type."""
        return {
            str: "class:pygments.literal.string",
            int: "class:pygments.literal.number",
            float: "class:pygments.literal.number",
            bool: "class:pygments.keyword.constant",
        }.get(type(value), "")

    def _format_value(self, value: Any) -> tuple[str, str]:
        """Return the formatted value and its style."""
        if isinstance(value, (list, dict)):
            length = len(value)
            if isinstance(value, list):
                return f" [] {length} items", "class:pygments.comment"
            return f" {{}} {length} items", "class:pygments.comment"
        return repr(value), self._get_value_style(value)

    def _get_formatted_text(self) -> StyleAndTextTuples:
        """Generate the complete tree view as formatted text."""
        result: StyleAndTextTuples = []
        line_paths: list[tuple[str, ...]] = []
        toggled_paths = self._toggled_paths
        start_expanded = self.start_expanded
        toggle = self._toggle
        format_value = self._format_value
        selected_line = self._selected_line

        def format_node(
            data: Any, path: tuple[str, ...], indent: int, key: str
        ) -> None:
            is_expanded = (path in toggled_paths) ^ start_expanded
            has_children = isinstance(data, (dict, list))
            mouse_handler = partial(toggle, path=path)
            current_line = len(line_paths)
            line_paths.append(path)

            value, style = format_value(data)

            # Highlight the selected line
            selected = current_line == selected_line
            sel_prefix = "class:tree.selected " if selected else ""

            row: StyleAndTextTuples = [
                # Add indentation
                (sel_prefix, "  " * indent),
                # Add toggle symbol
                (
                    (
                        sel_prefix + "class:pygments.operator",
                        "▼" if is_expanded else "▶",
                    )
                    if has_children
                    else (sel_prefix, " ")
                ),
                (sel_prefix, " "),
                (sel_prefix + "class:pygments.keyword", str(key)),
                (sel_prefix + "class:pygments.punctuation", ": "),
                (sel_prefix + style, value),
                ("", "\n"),
            ]

            # Apply mouse_handler to rows with children
            if has_children:
                row = [(s, text, mouse_handler) for (s, text, *_) in row]

            result.extend(row)

            if is_expanded and has_children:
                if isinstance(data, list):
                    data = {str(i): v for i, v in enumerate(data)}

                for k, v in data.items():
                    new_path = (*path, str(k)) if path else (str(k),)
                    format_node(v, new_path, indent + 1, k)

        format_node(self.data, (), 0, self.title)

        self._line_count = len(line_paths)
        self._line_paths = line_paths
        # Clamp selected line to valid range
        self._selected_line = max(0, min(self._selected_line, self._line_count - 1))

        return result

    def _toggle(
        self, mouse_event: MouseEvent, path: tuple[str, ...]
    ) -> NotImplementedOrNone:
        """Toggle the expansion state of a node."""
        if (
            mouse_event.button == MouseButton.LEFT
            and mouse_event.event_type == MouseEventType.MOUSE_DOWN
        ):
            get_app().layout.current_control = self._control
            return None
        if (
            mouse_event.button == MouseButton.LEFT
            and mouse_event.event_type == MouseEventType.MOUSE_UP
        ):
            if path in self._toggled_paths:
                self._toggled_paths.remove(path)
            else:
                self._toggled_paths.add(path)
            return None
        return NotImplemented

    def __pt_container__(self) -> Window:
        """Return the tree-view container's content."""
        return self.container
