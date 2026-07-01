"""Defines a logo widget."""

from __future__ import annotations

from apptk.application.current import get_app
from apptk.formatted_text.utils import pad
from apptk.layout.containers import Window, WindowAlign
from apptk.layout.controls import FormattedTextControl
from apptk.widgets.base import Label

from euporie.core import __version__

logo_micro = Label(" ⚈ ", style="class:menu,logo", width=3, dont_extend_width=True)


def logo_medium() -> Window:
    """Return a :py:class:`~apptk.layout.containers.Window` with the app's logo."""
    app_name = get_app().__class__.name
    return Window(
        content=FormattedTextControl(
            pad(
                [
                    ("fg:white", "•"),
                    ("fg:darkred", "▗▆██▆▖"),
                    ("fg:yellow", "*"),
                    ("", "\n"),
                    ("", " "),
                    ("fg:darkred", "████"),
                    ("fg:darkred bg:black reverse", "●"),
                    ("fg:darkred", "█"),
                    ("", " "),
                    ("bold", "euporie"),
                    ("", "\n"),
                    ("fg:orange", "."),
                    ("fg:darkred", "▝🮅██🮅▘"),
                    ("", " "),
                    ("dim", f"{app_name}"),
                    ("", " "),
                    ("fg:#888 dim", f"v{__version__}"),
                ]
            )
        ),
        height=3,
        dont_extend_width=False,
        wrap_lines=False,
        align=WindowAlign.CENTER,
    )


"""
    ⢠⣶⣿⣿⣶⡄  ▗▆██▆▖  ▗▆██▆▖  🭊🭂██🭍🬿  🭉🭂███🭍🬾  🬞🬹██🬹🬏
    ⣿⣿⣿⣿⣉⣿  ████𜶮█  ████●█  ████●█  ▐███🯩🯫▌  🬫██🯩🯫🬛
    ⠘⠿⣿⣿⠿⠃  ▝🮅██🮅▘  ▝🮅██🮅▘  🭥🭓██🭞🭚  🭤🭓███🭞🭙  🬁🬎██🬎🬀

"""
