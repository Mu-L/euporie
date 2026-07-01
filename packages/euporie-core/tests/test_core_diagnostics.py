"""Test module for euporie.core.diagnostics."""

from __future__ import annotations

from euporie.core.diagnostics import Diagnostic, Report


def _make_diagnostic(code: str = "E1") -> Diagnostic:
    """Return a sample diagnostic."""
    return Diagnostic(
        code=code,
        message="a message",
        level=3,
        link="https://example.com",
        lines=slice(0, 1),
        chars=slice(0, 5),
    )


def test_report_is_a_list() -> None:
    """A report behaves like a list of diagnostics."""
    diagnostic = _make_diagnostic()
    report = Report([diagnostic])
    assert len(report) == 1
    assert report[0] is diagnostic
    assert list(report) == [diagnostic]


def test_from_lsp_converts_ranges() -> None:
    """LSP output is converted into diagnostics with slices."""
    report = Report.from_lsp(
        "print()",
        [
            {
                "code": "E100",
                "message": "bad",
                "severity": 1,
                "codeDescription": {"href": "https://example.com"},
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 4},
                },
            }
        ],
    )
    assert len(report) == 1
    diagnostic = report[0]
    assert diagnostic.code == "E100"
    assert diagnostic.message == "bad"
    # severity 1 maps to level 4 (5 - severity)
    assert diagnostic.level == 4
    assert diagnostic.link == "https://example.com"
    assert diagnostic.lines == slice(0, 1)
    assert diagnostic.chars == slice(0, 5)


def test_from_lsp_uses_defaults() -> None:
    """Missing fields fall back to sensible defaults."""
    report = Report.from_lsp(
        "x",
        [
            {
                "range": {
                    "start": {"line": 2, "character": 1},
                    "end": {"line": 3, "character": 2},
                }
            }
        ],
    )
    diagnostic = report[0]
    assert diagnostic.code == ""
    assert diagnostic.message == ""
    # Default severity 2 maps to level 3
    assert diagnostic.level == 3
    assert diagnostic.link is None
    assert diagnostic.lines == slice(2, 4)
    assert diagnostic.chars == slice(1, 3)


def test_from_lsp_empty() -> None:
    """An empty LSP output produces an empty report."""
    report = Report.from_lsp("", [])
    assert len(report) == 0


def test_from_reports_flattens() -> None:
    """Multiple reports are flattened into a single report."""
    a = _make_diagnostic("A")
    b = _make_diagnostic("B")
    c = _make_diagnostic("C")
    combined = Report.from_reports(Report([a, b]), Report([c]))
    assert list(combined) == [a, b, c]


def test_from_reports_empty() -> None:
    """Combining no reports produces an empty report."""
    assert list(Report.from_reports()) == []
