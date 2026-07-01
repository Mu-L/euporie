"""Test module for euporie.core.history."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, NonCallableMock, patch

from euporie.core.history import KernelHistory, StateHistory


async def test_kernel_history_load_removes_sequential_duplicates() -> None:
    """Loading history removes sequential duplicate entries."""
    kernel = NonCallableMock()
    kernel.history_async = AsyncMock(
        return_value=[
            (0, 0, "a"),
            (0, 1, "a"),
            (0, 2, "b"),
            (0, 3, "a"),
        ]
    )
    history = KernelHistory(kernel)
    # history_async returns oldest-first; load yields most-recent first
    items = [item async for item in history.load()]
    assert items == ["a", "b", "a"]


async def test_kernel_history_load_empty() -> None:
    """Loading empty history yields nothing."""
    kernel = NonCallableMock()
    kernel.history_async = AsyncMock(return_value=[])
    history = KernelHistory(kernel)
    items = [item async for item in history.load()]
    assert items == []


def test_kernel_history_load_history_strings_empty() -> None:
    """The synchronous loader yields nothing."""
    history = KernelHistory(Mock())
    assert list(history.load_history_strings()) == []


def test_state_history_load_history_strings_reversed() -> None:
    """State history yields the most recent entries first."""
    app = Mock()
    app.state = SimpleNamespace(my_key=["a", "b", "c"])
    history = StateHistory("my_key")
    with patch("euporie.core.app.current.get_app", return_value=app):
        assert list(history.load_history_strings()) == ["c", "b", "a"]


def test_state_history_load_no_app() -> None:
    """Without an app, no history strings are yielded."""
    history = StateHistory("my_key")
    with patch("euporie.core.app.current.get_app", side_effect=Exception):
        assert list(history.load_history_strings()) == []


def test_state_history_store_string_appends() -> None:
    """Storing a string appends it to the state entries."""
    app = Mock()
    app.state = SimpleNamespace(my_key=["a"])
    history = StateHistory("my_key")
    with patch("euporie.core.app.current.get_app", return_value=app):
        history.store_string("b")
    assert app.state.my_key == ["a", "b"]


def test_state_history_store_string_enforces_max() -> None:
    """Storing enforces the maximum number of entries."""
    app = Mock()
    app.state = SimpleNamespace(my_key=["a", "b"])
    history = StateHistory("my_key", max_entries=2)
    with patch("euporie.core.app.current.get_app", return_value=app):
        history.store_string("c")
    assert app.state.my_key == ["b", "c"]


def test_state_history_store_string_no_app() -> None:
    """Storing without an app does not raise."""
    history = StateHistory("my_key")
    with patch("euporie.core.app.current.get_app", side_effect=Exception):
        history.store_string("b")
