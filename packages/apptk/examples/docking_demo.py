"""Demo application for the DockingSplit container."""

from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

from apptk.application import Application
from apptk.key_binding.key_bindings import KeyBindings
from apptk.layout.containers import HSplit, Window
from apptk.layout.controls import FormattedTextControl
from apptk.layout.layout import Layout
from apptk.styles.style import Style
from apptk.widgets.docking import DockingPanel, DockingSplit

if TYPE_CHECKING:
    from apptk.key_binding.key_processor import KeyPressEvent


def create_panel_content(name: str, color: str) -> Window:
    """Create a simple colored panel with a label.

    Args:
        name: The name to display in the panel.
        color: The background color style.

    Returns:
        A Window containing the panel content.
    """
    return Window(
        FormattedTextControl(
            f" This is the '{name}' panel.\n\n"
            f" Drag tabs to dock them in different positions:\n"
            f"   \u2022 Left edge \u2192 tile left\n"
            f"   \u2022 Right edge \u2192 tile right\n"
            f"   \u2022 Top edge \u2192 tile above\n"
            f"   \u2022 Bottom edge \u2192 tile below\n"
            f"   \u2022 Center \u2192 add as tab\n"
        ),
        style=color,
    )


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
        DockingPanel(
            title="Panel 1",
            content=create_panel_content("Panel 1", "bg:ansiblue fg:ansiwhite"),
        ),
        DockingPanel(
            title="Panel 2",
            content=create_panel_content("Panel 2", "bg:ansigreen fg:ansiblack"),
        ),
        DockingPanel(
            title="Panel 3",
            content=create_panel_content("Panel 3", "bg:ansired fg:ansiwhite"),
        ),
        DockingPanel(
            title="Panel 4",
            content=create_panel_content("Panel 4", "bg:ansiyellow fg:ansiblack"),
            closeable=True,
        ),
        DockingPanel(
            title="Panel 5",
            content=create_panel_content("Panel 5", "bg:ansimagenta fg:ansiwhite"),
            closeable=True,
        ),
    ]

    docking = DockingSplit(panels=panels)

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
