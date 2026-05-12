"""Editor resolution and editing utilities."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import TYPE_CHECKING

from apptk.application.current import get_app

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Callable


def resolve_editor(cmd: str | None = None) -> str | None:
    """Resolve an editor command from explicit value, env vars, or fallbacks.

    Args:
        cmd: An explicit editor command string, or None.

    Returns:
        The resolved editor command string, or None if no editor found.
    """
    if cmd:
        return cmd

    visual = os.environ.get("VISUAL")
    if visual:
        return visual

    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Fallback to common editors
    for fallback in [
        "editor",
        "micro",
        "nano",
        "pico",
        "vi",
        "emacs",
    ]:
        if shutil.which(fallback):
            return fallback

    return None


def _default_position() -> dict[str, int]:
    """Return a fallback editor position dict.

    Returns:
        A dict with keys left, top, width, height, bottom, right.
    """
    try:
        size = get_app().output.get_size()
        return {
            "left": 0,
            "top": 0,
            "width": size.columns,
            "height": size.rows,
            "bottom": size.rows,
            "right": size.columns,
        }
    except Exception:
        return {
            "left": 0,
            "top": 0,
            "width": 80,
            "height": 24,
            "bottom": 24,
            "right": 80,
        }


async def run_editor(
    filename: str,
    cmd: str | None = None,
    get_position: Callable[[], dict[str, int] | None] | None = None,
) -> bool:
    """Run an editor on a file.

    Resolves the editor command, optionally formats it with position placeholders
    for foreground editing, and runs the editor.

    Args:
        filename: Path to the file to edit.
        cmd: Explicit editor command, or None to resolve from env.
        get_position: Optional callable returning a dict with keys
            ``left``, ``top``, ``width``, ``height``, ``bottom``, ``right``
            for foreground editors that accept position placeholders.

    Returns:
        True if the editor exited successfully.
    """
    from apptk.application.run_in_terminal import run_in_terminal

    resolved_cmd = resolve_editor(cmd)
    if resolved_cmd is None:
        return False

    run_in_foreground = "{left}" in resolved_cmd

    if run_in_foreground:
        pos = (get_position() if get_position else None) or _default_position()
        formatted_cmd = resolved_cmd.format(**pos)
        returncode = subprocess.call([*shlex.split(formatted_cmd), filename])  # noqa: ASYNC221
        return returncode == 0
    else:

        def _edit() -> bool:
            try:
                returncode = subprocess.call([*shlex.split(resolved_cmd), filename])
                return returncode == 0
            except OSError:
                return False

        return await run_in_terminal(_edit, in_executor=True)


def edit_in_editor(
    filename: str,
    line_number: int = 0,
    cmd: str | None = None,
    get_position: Callable[[], dict[str, int] | None] | None = None,
) -> asyncio.Task[None]:
    """Fire-and-forget editor launch for a file.

    This is a convenience wrapper around :func:`run_editor` that creates a
    background task. Used by kernel ``%edit`` magic.

    Args:
        filename: The path to the file to edit.
        line_number: The line number to open the editor at (unused currently).
        cmd: Explicit editor command, or None to resolve from env.
        get_position: Optional callable for foreground editor positioning.

    Returns:
        The background asyncio Task.
    """

    async def _run() -> None:
        await run_editor(filename, cmd=cmd, get_position=get_position)

    return get_app().create_background_task(_run())
