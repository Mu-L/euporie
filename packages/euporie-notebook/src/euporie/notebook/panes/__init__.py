"""Panes for use in euporie notebook editor."""

from apptk.convert.mime import MIME_FORMATS
from apptk.filters.environment import have_modules

from euporie.core.nbformat import NOTEBOOK_EXTENSIONS
from euporie.core.panes import _PANE_REGISTRY, PaneRegistryEntry

_PANE_REGISTRY.extend(
    [
        PaneRegistryEntry(
            path="euporie.notebook.panes.display:DisplayPane",
            name="File Viewer",
            mime_types=set(MIME_FORMATS.keys()),
        ),
        PaneRegistryEntry(
            path="euporie.notebook.panes.edit:EditorPane",
            name="Text Editor",
            mime_types={"text/*"},
            weight=1,
        ),
        PaneRegistryEntry(
            path="euporie.notebook.panes.json:JsonPane",
            name="JSON Viewer",
            mime_types={"*json"},
            file_extensions={".json": None},
        ),
        PaneRegistryEntry(
            path="euporie.notebook.panes.notebook:Notebook",
            name="Notebook Editor",
            mime_types={"application/x-ipynb+json"},
            file_extensions=dict.fromkeys(NOTEBOOK_EXTENSIONS),
            weight=3,
        ),
        PaneRegistryEntry(
            path="euporie.notebook.panes.console:Console",
            name="Console",
        ),
        PaneRegistryEntry(
            path="euporie.notebook.panes.web:WebPane",
            name="Web Viewer",
            mime_types={"text/html", "text/markdown"},
            weight=2,
        ),
    ]
)

if have_modules("ptterm")():
    _PANE_REGISTRY.append(
        PaneRegistryEntry(
            path="euporie.notebook.panes.terminal:TerminalPane",
            name="Terminal",
        )
    )
