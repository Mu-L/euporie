"""Test module for euporie.core.utils."""

from __future__ import annotations

import pytest
from apptk.data_structures import Point
from apptk.mouse_events import MouseButton, MouseEvent, MouseEventType

from euporie.core.utils import (
    ChainedList,
    dict_merge,
    import_submodules,
    on_click,
    root_module,
)


def test_ChainedList() -> None:
    """Test ChainedList."""
    cl = ChainedList([1, 2, 3], [4, 5, 6])
    assert len(cl) == 6
    assert cl[3] == 4
    assert cl[1:4] == [2, 3, 4]


def test_ChainedList_empty() -> None:
    """An empty ChainedList has zero length."""
    cl: ChainedList[int] = ChainedList()
    assert len(cl) == 0
    assert list(cl) == []


def test_ChainedList_iteration() -> None:
    """A ChainedList iterates over all chained items in order."""
    cl = ChainedList([1], [], [2, 3])
    assert list(cl) == [1, 2, 3]


def test_ChainedList_reflects_mutation() -> None:
    """A ChainedList reflects mutations to the underlying lists."""
    first = [1, 2]
    cl = ChainedList(first, [3])
    first.append(99)
    assert list(cl) == [1, 2, 99, 3]


def test_dict_merge() -> None:
    """Test dict_merge."""
    target_dict = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
    input_dict = {"b": {"c": 4}, "e": [3, 4], "f": 5}

    dict_merge(target_dict, input_dict)
    assert target_dict == {"a": 1, "b": {"c": 4, "d": 3}, "e": [1, 2, 3, 4], "f": 5}


def test_dict_merge_overwrites_scalar() -> None:
    """A scalar value overwrites an existing scalar."""
    target = {"a": 1}
    dict_merge(target, {"a": 2})
    assert target == {"a": 2}


def test_dict_merge_type_mismatch_overwrites() -> None:
    """Merging mismatched types replaces the target value."""
    target = {"a": {"nested": 1}}
    dict_merge(target, {"a": [1, 2]})
    assert target == {"a": [1, 2]}


def test_dict_merge_empty_input() -> None:
    """Merging an empty dict leaves the target unchanged."""
    target = {"a": 1}
    dict_merge(target, {})
    assert target == {"a": 1}


def _click(button: MouseButton, event_type: MouseEventType) -> MouseEvent:
    """Return a mouse event for the given button and event type."""
    return MouseEvent(
        position=Point(0, 0),
        button=button,
        event_type=event_type,
        modifiers=frozenset(),
    )


def test_on_click_calls_on_left_up() -> None:
    """The handler calls the function on a left mouse-up."""
    result = ""

    def click_handler() -> None:
        nonlocal result
        result = "Clicked!"

    handler = on_click(click_handler)
    assert handler(_click(MouseButton.LEFT, MouseEventType.MOUSE_UP)) is None
    assert result == "Clicked!"


def test_on_click_ignores_other_button() -> None:
    """The handler is a no-op for non-left buttons."""
    result = ""

    def click_handler() -> None:
        nonlocal result
        result = "Clicked!"

    handler = on_click(click_handler)
    assert handler(_click(MouseButton.RIGHT, MouseEventType.MOUSE_UP)) is NotImplemented
    assert result == ""


def test_on_click_ignores_other_event_type() -> None:
    """The handler is a no-op for non mouse-up events."""
    result = ""

    def click_handler() -> None:
        nonlocal result
        result = "Clicked!"

    handler = on_click(click_handler)
    assert (
        handler(_click(MouseButton.LEFT, MouseEventType.MOUSE_DOWN)) is NotImplemented
    )
    assert result == ""


def test_on_click_returns_function_result() -> None:
    """The handler returns the wrapped function's return value."""
    handler = on_click(lambda: NotImplemented)
    assert handler(_click(MouseButton.LEFT, MouseEventType.MOUSE_UP)) is NotImplemented


def test_root_module_resolves_to_top_level() -> None:
    """root_module walks up to the topmost package with a location."""
    root = root_module("euporie.core.utils")
    # `euporie` is a namespace package with no location, so the walk
    # stops at `euporie.core`.
    assert root.__name__ == "euporie.core"


def test_root_module_of_top_level() -> None:
    """Passing a top-level package returns that module."""
    root = root_module("euporie.core")
    assert root.__name__ == "euporie.core"


def test_root_module_missing() -> None:
    """An unknown module name raises ModuleNotFoundError."""
    with pytest.raises(ModuleNotFoundError):
        root_module("definitely_not_a_real_module_xyz")


def test_import_submodules_finds_matches() -> None:
    """import_submodules imports submodules matching a given name."""
    import euporie.core

    modules = import_submodules(euporie.core, ("utils",))
    names = [m.__name__ for m in modules]
    assert "euporie.core.utils" in names


def test_import_submodules_no_matches() -> None:
    """import_submodules returns an empty list when no submodules match."""
    import euporie.core

    modules = import_submodules(euporie.core, ("definitely_not_a_real_submodule",))
    assert modules == []
