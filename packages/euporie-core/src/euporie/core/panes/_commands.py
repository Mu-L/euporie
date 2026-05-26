"""Contains commands for tabs."""

from __future__ import annotations

import logging
from pathlib import Path

from apptk.application.current import get_app
from apptk.commands import add_cmd
from apptk.filters import (
    buffer_has_focus,
)
from apptk.filters.app import display_has_focus
from apptk.filters.buffer import buffer_is_code, buffer_is_empty

from euporie.core.filters import (
    kernel_pane_has_focus,
    pane_can_save,
    pane_has_focus,
    pane_type_has_focus,
)
from euporie.core.panes.kernel import KernelPane

log = logging.getLogger(__name__)


@add_cmd(filter=pane_can_save, aliases=["save", "w"], keys=["c-s"])
def _save_file(path: str = "") -> None:
    """Save the current file."""
    if (tab := get_app().pane) is not None:
        from upath import UPath

        try:
            tab._save(UPath(path) if path else None)
        except NotImplementedError:
            pass


@add_cmd(aliases=["wq", "x"])
def _save_and_quit(path: str = "") -> None:
    """Save the current tab then quits euporie."""
    app = get_app()
    if (tab := app.pane) is not None:
        from upath import UPath

        try:
            tab.save(UPath(path) if path else None)
        except NotImplementedError:
            pass

    app.exit()


@add_cmd(
    keys=["A-s"],
    menu_title="Save As…",
    filter=pane_can_save,
)
def _save_as(path: str = "") -> None:
    """Save the current file at a new location."""
    if path:
        _save_file(path)
    else:
        app = get_app()
        if dialog := app.get_dialog("save-as"):
            dialog.show(tab=app.pane)


@add_cmd(
    keys=["f5"],
    aliases=["reset-tab"],
    filter=pane_has_focus,
    title="Refresh the current tab",
)
def _refresh_tab() -> None:
    """Reload the tab contents and reset the tab."""
    if (tab := get_app().pane) is not None:
        if tab.path is not None:
            tab.read_file(tab.path)
        tab.reset()


@add_cmd(
    bindings=[
        {
            "keys": [("i", "i")],
            "filter": kernel_pane_has_focus & ~buffer_has_focus & ~display_has_focus,
        },
        {
            "filter": buffer_is_code
            & buffer_is_empty
            & pane_type_has_focus("euporie.core.panes.console:BaseConsole"),
            "keys": ["c-c", "<sigint>"],
        },
    ]
)
def _interrupt_kernel() -> None:
    """Interrupt the notebook's kernel."""
    if isinstance(kt := get_app().pane, KernelPane):
        kt.interrupt_kernel()


@add_cmd(
    keys=[("0", "0")],
    filter=kernel_pane_has_focus & ~buffer_has_focus & ~display_has_focus,
)
def _restart_kernel() -> None:
    """Restart the notebook's kernel."""
    if isinstance(kt := get_app().pane, KernelPane):
        kt.restart_kernel()


@add_cmd(aliases=["pipe"], filter=pane_has_focus)
async def _pipe_tab(*cmd: str) -> None:
    """Pipe the current file through an external command."""
    import tempfile

    from apptk.application.edit import run_editor
    from upath import UPath

    app = get_app()

    resolved_cmd = " ".join(cmd) if cmd else None
    if not resolved_cmd:
        resolved_cmd = getattr(app.config, "external_editor", None) or None

    tab = app.pane
    if tab is None:
        return

    # Write current state to memory
    mem_path = UPath("memory:///_euporie_pipe_tmp")
    try:
        tab.write_file(mem_path)
    except NotImplementedError:
        log.warning("Current tab does not support writing")
        return

    # Read the in-memory file contents and write to a real tempfile
    try:
        input_data = mem_path.read_bytes()
    finally:
        try:
            mem_path.unlink()
        except (FileNotFoundError, OSError):
            pass

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=tab.path.suffix, delete=False) as tmp:
            tmp.write(input_data)
            tmp_path = Path(tmp.name)

        success = await run_editor(str(tmp_path), cmd=resolved_cmd)

        if not success:
            return

        result_data = tmp_path.read_bytes()
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    # Write output back to memory and read it into the tab
    try:
        mem_path.write_bytes(result_data)
    except OSError:
        log.error("Failed to write pipe output to memory")
        return

    try:
        tab.read_file(mem_path)
        tab.dirty = True
    except NotImplementedError:
        log.warning("Current tab does not support reading")
    finally:
        try:
            mem_path.unlink()
        except (FileNotFoundError, OSError):
            pass

    tab.reset()
