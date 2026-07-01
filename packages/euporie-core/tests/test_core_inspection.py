"""Test module for euporie.core.inspection."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, NonCallableMock

from apptk.document import Document

from euporie.core.inspection import (
    FirstInspector,
    Inspector,
    KernelInspector,
    LspInspector,
)


def test_kernel_inspector_kernel_callable() -> None:
    """A callable kernel is resolved on access."""
    kernel = NonCallableMock()
    inspector = KernelInspector(lambda: kernel)
    assert inspector.kernel is kernel


def test_kernel_inspector_kernel_direct() -> None:
    """A non-callable kernel is returned directly."""
    kernel = NonCallableMock()
    inspector = KernelInspector(kernel)
    assert inspector.kernel is kernel


async def test_kernel_inspector_get_context() -> None:
    """get_context delegates to the kernel's inspect_async."""
    kernel = NonCallableMock()
    kernel.inspect_async = AsyncMock(return_value={"text/plain": "help"})
    inspector = KernelInspector(kernel)
    document = Document("foo", cursor_position=2)
    result = await inspector.get_context(document, auto=False)
    kernel.inspect_async.assert_awaited_once_with("foo", 2)
    assert result == {"text/plain": "help"}


async def test_lsp_inspector_get_context() -> None:
    """get_context delegates to the LSP client's hover_."""
    lsp = NonCallableMock()
    lsp.hover_ = AsyncMock(return_value={"contents": "info"})
    path = Mock()
    inspector = LspInspector(lsp, path)
    document = Document("line1\nline2", cursor_position=8)
    result = await inspector.get_context(document, auto=True)
    lsp.hover_.assert_awaited_once_with(
        path=path,
        line=document.cursor_position_row,
        char=document.cursor_position_col,
    )
    assert result == {"contents": "info"}


def _mock_inspector(result: dict) -> Inspector:
    """Return an inspector whose get_context yields the given result."""
    inspector = NonCallableMock(spec=Inspector)
    inspector.get_context = AsyncMock(return_value=result)
    return inspector


async def test_first_inspector_returns_first_non_empty() -> None:
    """FirstInspector returns the first non-empty result."""
    inspectors = [_mock_inspector({}), _mock_inspector({"a": 1})]
    first = FirstInspector(inspectors)
    result = await first.get_context(Document("x"), auto=False)
    assert result == {"a": 1}


async def test_first_inspector_empty_when_all_empty() -> None:
    """FirstInspector returns an empty dict when all inspectors are empty."""
    inspectors = [_mock_inspector({}), _mock_inspector({})]
    first = FirstInspector(inspectors)
    result = await first.get_context(Document("x"), auto=False)
    assert result == {}


async def test_first_inspector_supports_callable_inspectors() -> None:
    """FirstInspector accepts a callable that returns the inspectors."""
    inspector = _mock_inspector({"b": 2})
    first = FirstInspector(lambda: [inspector])
    result = await first.get_context(Document("x"), auto=False)
    assert result == {"b": 2}


async def test_first_inspector_no_inspectors() -> None:
    """FirstInspector with no inspectors returns an empty dict."""
    first = FirstInspector([])
    result = await first.get_context(Document("x"), auto=False)
    assert result == {}
