"""Extended Buffer with configurable editor support."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from apptk.application.current import get_app
from prompt_toolkit import buffer as ptk_buffer
from prompt_toolkit.buffer import *  # noqa: F403

if TYPE_CHECKING:
    import asyncio


class Buffer(ptk_buffer.Buffer):
    """Extended Buffer with configurable editor command and foreground editing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the buffer."""
        super().__init__(*args, **kwargs)

    def _get_editor_position(self) -> dict[str, int] | None:
        """Find the Window containing this buffer and return its position.

        Returns:
            A dict with keys left, top, width, height, bottom, right, or None.
        """
        from apptk.layout.controls import BufferControl

        try:
            app = get_app()
        except Exception:
            return None

        for window in app.layout.find_all_windows():
            if (
                hasattr(window, "content")
                and isinstance(window.content, BufferControl)
                and window.content.buffer is self
            ):
                info = window.render_info
                if info is None:
                    return None

                margin_left = sum(
                    window._get_margin_width(m) for m in window.left_margins
                )
                margin_right = sum(
                    window._get_margin_width(m) for m in window.right_margins
                )
                top = info._y_offset
                left = info._x_offset - margin_left
                width = info.window_width + margin_left + margin_right
                height = min(app.output.get_size().rows, info.window_height)

                return {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                    "bottom": top + height,
                    "right": left + width,
                }

        return None

    def open_in_editor(
        self,
        validate_and_handle: bool = False,
        cmd: str | None = None,
    ) -> asyncio.Task[None]:
        """Open buffer in editor, with support for custom commands and foreground editing.

        Args:
            validate_and_handle: Whether to validate and handle after editing.
            cmd: An explicit editor command to use.

        Returns:
            An asyncio Task for the editing operation.
        """
        from apptk.application.edit import run_editor
        from apptk.document import Document

        if self.read_only():
            raise ptk_buffer.EditReadOnlyBuffer()

        # Write current text to temporary file
        if self.tempfile:
            filename, cleanup_func = self._editor_complex_tempfile()
        else:
            filename, cleanup_func = self._editor_simple_tempfile()

        async def run() -> None:
            try:
                success = await run_editor(
                    filename,
                    cmd=cmd,
                    get_position=self._get_editor_position,
                )

                # Read content again
                if success:
                    text = Path(filename).read_text(encoding="utf-8")

                    # Drop trailing newline
                    if text.endswith("\n"):
                        text = text[:-1]

                    self.document = Document(text=text, cursor_position=len(text))

                    # Accept the input
                    if validate_and_handle:
                        self.validate_and_handle()

            finally:
                cleanup_func()

        return get_app().create_background_task(run())
