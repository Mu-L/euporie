"""Responsible for loading data from urls."""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING

from upath.implementations.memory import MemoryPath

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping
    from pathlib import Path
    from typing import IO, Any


log = logging.getLogger(__name__)


def safe_write(
    path: Path,
    *,
    mode: str = "w",
    create_backup: bool = False,
) -> Generator[IO, None, None]:
    """Write to a file atomically using a temporary file and rename.

    Writes to a temporary file alongside the target, then atomically renames
    it into place. Optionally creates a numbered backup of the original file
    via hard link before replacing it.

    Args:
        path: The target file path.
        mode: File open mode ("w" for text, "wb" for binary).
        create_backup: Whether to create a numbered backup of the original.

    Yields:
        A file object to write to.

    Raises:
        BaseException: Re-raises any exception from the writing block after cleanup.
    """
    tmp_path = path.with_name(path.name + ".tmp")
    succeeded = False
    fp = tmp_path.open(mode)
    try:
        yield fp
        succeeded = True
    finally:
        fp.close()
        if not succeeded:
            with suppress(FileNotFoundError):
                tmp_path.unlink()
        else:
            if create_backup:
                count = 0
                while True:
                    backup = path.with_name(f"{path.name}.bak.{count}")
                    if not backup.exists():
                        break
                    count += 1
                with suppress(FileNotFoundError):
                    backup.hardlink_to(path)
            tmp_path.rename(path)


safe_write = contextmanager(safe_write)


# Define custom universal_pathlib path implementations


class UntitledPath(MemoryPath):
    """A path for untitled files, as needed for LSP servers."""

    @classmethod
    def _parse_storage_options(
        cls, urlpath: str, protocol: str, storage_options: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Parse storage_options from the urlpath."""
        return {}

    def exists(self, *, follow_symlinks: bool = True) -> bool:
        """Untitled files are unsaved and do not exist."""
        return False
