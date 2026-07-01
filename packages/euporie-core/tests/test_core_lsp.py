"""Test module for euporie.core.lsp."""

from __future__ import annotations

from euporie.core.lsp import range_to_slice


def test_range_to_slice_single_line() -> None:
    """A range within a single line maps to character positions."""
    text = "hello world"
    result = range_to_slice(0, 0, 0, 5, text)
    assert result == slice(0, 5)
    assert text[result] == "hello"


def test_range_to_slice_multi_line() -> None:
    """A range spanning multiple lines accounts for newline characters."""
    text = "abc\ndef\nghi"
    result = range_to_slice(1, 0, 2, 3, text)
    assert text[result] == "def\nghi"


def test_range_to_slice_partial_lines() -> None:
    """A range with character offsets on start and end lines."""
    text = "abc\ndef\nghi"
    result = range_to_slice(0, 1, 2, 1, text)
    assert text[result] == "bc\ndef\ng"


def test_range_to_slice_empty_range() -> None:
    """A zero-width range produces an empty slice."""
    text = "abc\ndef"
    result = range_to_slice(1, 1, 1, 1, text)
    assert text[result] == ""
