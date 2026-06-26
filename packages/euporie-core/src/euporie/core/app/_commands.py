"""Contains commands common to all euporie applications."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apptk.application.current import get_app
from apptk.commands import add_cmd
from apptk.filters import buffer_has_focus
from apptk.filters.buffer import cursor_at_start_of_line

from euporie.core.filters import pane_has_focus, pane_type_has_focus

if TYPE_CHECKING:
    from apptk.key_binding.key_processor import KeyPressEvent


@add_cmd(keys=["c-q", "<sigint>"], aliases=["q"])
def _quit() -> None:
    """Quit euporie."""
    get_app().exit()


@add_cmd(aliases=["q!"])
def _force_quit() -> None:
    """Quit euporie without saving any changes."""
    from apptk.application.application import Application

    Application.exit(get_app())


@add_cmd(
    keys=["c-o"],
    menu_title="Open file…",
    aliases=["open", "o"],
    icon="",
    style="class:purple",
)
def _open_file(path: str = "") -> None:
    """Open a file."""
    if path:
        from upath import UPath

        get_app().open_file(UPath(path))
    else:
        if dialog := get_app().get_dialog("open-file"):
            dialog.show()


@add_cmd(keys=["c-w"], aliases=["bc"], filter=pane_has_focus, menu_title="Close File")
def _close_tab() -> None:
    """Close the current tab."""
    get_app().close_tab()


@add_cmd(keys=["c-pagedown"], aliases=["bn"], filter=pane_has_focus)
def _next_tab() -> None:
    """Switch to the next tab."""
    get_app().tab_idx += 1


@add_cmd(keys=["c-pageup"], aliases=["bp"], filter=pane_has_focus)
def _previous_tab() -> None:
    """Switch to the previous tab."""
    get_app().tab_idx -= 1


@add_cmd(keys=["tab"], filter=~buffer_has_focus)
def _focus_next() -> None:
    """Focus the next control."""
    get_app().layout.focus_next()


@add_cmd(
    bindings=[
        {
            "keys": ["s-tab"],
            "filter": ~buffer_has_focus | (buffer_has_focus & cursor_at_start_of_line),
        },
    ]
)
def _focus_previous() -> None:
    """Focus the previous control."""
    get_app().layout.focus_previous()


@add_cmd(keys=["c-l"])
def _clear_screen() -> None:
    """Clear the screen."""
    get_app().renderer.clear()


@add_cmd(filter=buffer_has_focus)
async def _pipe_buffer(*cmd: str) -> None:
    """Pipe the current buffer through an external command."""
    app = get_app()
    buffer = app.current_buffer
    if cmd:
        resolved_cmd = " ".join(cmd)
    else:
        resolved_cmd = getattr(app.config, "external_editor", None) or None
    validate = getattr(app.config, "run_after_external_edit", False)
    await buffer.open_in_editor(validate_and_handle=validate, cmd=resolved_cmd)


@add_cmd(hidden=True)
def _notify(
    *message: str,
    timeout: float = 3.0,
    placement: str = "top-right",
    offset: int = 2,
    **kwargs: str,
) -> None:
    """Display a message in a non-interactive popup notification."""
    get_app().notify(
        " ".join(str(x) for x in message),
        timeout=timeout,
        placement=placement,
        offset=offset,
        class_=kwargs.get("class", ""),
    )


@add_cmd(hidden=True, aliases=[""])
def _go_to(event: KeyPressEvent, index: int = 0) -> None:
    """Go to a line or cell by number."""
    index = max(0, index - 1)
    if buffer_has_focus():
        buffer = get_app().current_buffer
        buffer.cursor_position = len("".join(buffer.text.splitlines(True)[:index]))
    elif pane_type_has_focus("euporie.notebook.panes.notebook:Notebook")():
        from euporie.notebook.panes.notebook import Notebook

        if isinstance(nb := get_app().pane, Notebook):
            nb.select(index)
