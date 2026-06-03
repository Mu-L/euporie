"""Demo application for the DockingSplit container."""

from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

from apptk.application import Application
from apptk.application.current import get_app
from apptk.key_binding.key_bindings import KeyBindings
from apptk.layout.containers import HSplit, Window
from apptk.layout.controls import FormattedTextControl
from apptk.layout.layout import Layout
from apptk.layout.mouse import MouseHandlerWrapper
from apptk.mouse_events import MouseButton, MouseEventType
from apptk.styles.style import Style
from apptk.widgets.docking import DockingSplit
from apptk.widgets.panel import Panel

if TYPE_CHECKING:
    from apptk.key_binding.key_bindings import NotImplementedOrNone
    from apptk.key_binding.key_processor import KeyPressEvent
    from apptk.mouse_events import MouseEvent


def create_panel_content(name: str, color: str) -> MouseHandlerWrapper:
    """Create a simple colored, focusable panel with a label.

    Clicking the panel focuses its content window.

    Args:
        name: The name to display in the panel.
        color: The background color style.

    Returns:
        A focusable container with a click-to-focus mouse handler.
    """
    window = Window(
        FormattedTextControl(
            f" This is the '{name}' panel.\n\n"
            f" Drag tabs to dock them in different positions:\n"
            f"   \u2022 Left edge \u2192 tile left\n"
            f"   \u2022 Right edge \u2192 tile right\n"
            f"   \u2022 Top edge \u2192 tile above\n"
            f"   \u2022 Bottom edge \u2192 tile below\n"
            f"   \u2022 Center \u2192 add as tab\n",
            focusable=True,
        ),
        style=color,
    )

    def mouse_handler(mouse_event: MouseEvent) -> NotImplementedOrNone:
        """Focus the window when clicked."""
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and mouse_event.button == MouseButton.LEFT
        ):
            get_app().layout.focus(window)
            return None
        return NotImplemented

    return MouseHandlerWrapper(content=window, handler=mouse_handler)


def main() -> None:
    """Run the docking demo application."""
    parser = argparse.ArgumentParser(description="Docking Split Demo")
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to a log file. Logging is disabled if not provided.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: DEBUG).",
    )
    args = parser.parse_args()

    if args.log_file:
        logging.basicConfig(
            filename=args.log_file,
            level=getattr(logging, args.log_level),
            format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        )

    # Create panels with different colors for visibility
    panels = [
        Panel(
            title="Panel 1",
            content=create_panel_content("Panel 1", "bg:ansiblue fg:ansiwhite"),
        ),
        Panel(
            title="Panel 2",
            content=create_panel_content("Panel 2", "bg:ansigreen fg:ansiblack"),
        ),
        Panel(
            title="Panel 3",
            content=create_panel_content("Panel 3", "bg:ansired fg:ansiwhite"),
        ),
        Panel(
            title="Panel 4",
            content=create_panel_content("Panel 4", "bg:ansiyellow fg:ansiblack"),
            closeable=True,
        ),
        Panel(
            title="Panel 5",
            content=create_panel_content("Panel 5", "bg:ansimagenta fg:ansiwhite"),
            closeable=True,
        ),
    ]

    docking = DockingSplit(panels=panels, activate_on_focus=True)

    # Key bindings
    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("c-q")
    def _exit(event: KeyPressEvent) -> None:
        """Exit the application."""
        event.app.exit()

    # Create the application layout
    layout = HSplit(
        [
            Window(
                FormattedTextControl(
                    " Docking Demo - Drag tabs to rearrange | Ctrl-C to quit"
                ),
                height=1,
                style="bg:ansibrightblack fg:ansiwhite bold",
            ),
            docking,
        ]
    )

    # Style inspired by euporie's tabbed_split_styles / tab_bar_styles
    style = Style.from_dict(
        {
            # Tab bar background
            "docking tab-bar": "bg:#1e1e1e",
            # Inactive tabs
            "inactive tab border top": "fg:#555555",
            "inactive tab border left": "fg:#555555",
            "inactive tab border right": "fg:#555555",
            "inactive tab title": "fg:#888888 bg:#2a2a2a",
            "inactive tab close": "fg:#666666",
            # Active tabs
            "active tab border top": "fg:#569cd6 bold",
            "active tab border left": "fg:#888888",
            "active tab border right": "fg:#888888",
            "active tab title": "fg:#ffffff bg:#1e1e1e bold",
            "active tab close": "fg:#cc4444",
            # Bottom border between tabs and content
            "border bottom": "fg:#888888",
            # Overflow scroll indicators
            "overflow": "fg:#888888",
            # Docking group
            "docking group": "",
            "docking-split": "",
        }
    )

    app: Application = Application(
        layout=Layout(layout),
        key_bindings=kb,
        full_screen=True,
        mouse_support=True,
        style=style,
    )

    app.run()


if __name__ == "__main__":
    main()
