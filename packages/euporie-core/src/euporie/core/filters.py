"""Define common filters."""

from __future__ import annotations

from functools import cache

from apptk.application.current import get_app
from apptk.filters import (
    Condition,
    has_completions,
)


@cache
def config_filter(name: str) -> Condition:
    """Create a filter that checks a boolean config setting.

    Args:
        name: The name of the config setting to check.

    Returns:
        A condition that evaluates to the current value of the setting.
    """

    def _check() -> bool:
        try:
            return bool(getattr(get_app().config.filters, name)())
        except Exception:
            return True

    return Condition(_check)


@Condition
def has_panes() -> bool:
    """Filter to show if any panes are open in an app."""
    return bool(get_app().panes)


@Condition
def has_dialog() -> bool:
    """Determine if a dialog is being displayed."""
    from apptk.layout.containers import ConditionalContainer

    app = get_app()
    for dialog in app.dialogs.values():
        if isinstance(dialog.content, ConditionalContainer) and dialog.content.filter():
            return True
    return False


@Condition
def has_menus() -> bool:
    """Determine if a menu is being displayed."""
    from apptk.layout.containers import ConditionalContainer

    from euporie.notebook.current import get_app

    app = get_app()
    for menu in app.menus.values():
        if isinstance(menu.content, ConditionalContainer) and menu.content.filter():
            return True
    return False


has_float = has_dialog | has_menus | has_completions


@Condition
def pane_has_focus() -> bool:
    """Determine if there is a currently focused pane."""
    return get_app().pane is not None


@Condition
def kernel_pane_has_focus() -> bool:
    """Determine if there is a focused kernel pane."""
    from euporie.core.panes.kernel import KernelPane

    return isinstance(get_app().pane, KernelPane)


@cache
def pane_type_has_focus(pane_class_path: str) -> Condition:
    """Determine if the focused tab is of a particular type."""
    from pkgutil import resolve_name

    pane_class = cache(resolve_name)

    return Condition(lambda: isinstance(get_app().pane, pane_class(pane_class_path)))


@Condition
def pane_can_save() -> bool:
    """Determine if the current pane can save it's contents."""
    from euporie.core.panes.base import Pane

    return (
        pane := get_app().pane
    ) is not None and pane.__class__.write_file != Pane.write_file


@Condition
def pager_has_focus() -> bool:
    """Determine if the pager is focused."""
    app = get_app()
    pager = app.pager
    if pager is not None:
        return app.layout.has_focus(pager)
    return False


@Condition
def kernel_is_python() -> bool:
    """Determine if the current pane has a python kernel."""
    from euporie.core.panes.kernel import KernelPane

    kernel_pane = get_app().pane
    if isinstance(kernel_pane, KernelPane):
        return kernel_pane.language == "python"
    return False


@Condition
def multiple_cells_selected() -> bool:
    """Determine if there is more than one selected cell."""
    from euporie.core.panes.notebook import BaseNotebook

    nb = get_app().pane
    if isinstance(nb, BaseNotebook):
        return len(nb.selected_indices) > 1
    return False
